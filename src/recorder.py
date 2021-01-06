from config import config

from imutils.video import VideoStream
import datetime
import pytz
import imutils
from time import sleep, time
import cv2
import numpy as np
import os
import astral.sun
from sys import platform

def start_recorder(queue = None, debug = False):
    vs = VideoStream(src=0, resolution=config.MD_RESOLUTION, usePiCamera='linux' in platform)
    vs_stream = vs.start()

    sleep(2.0)

    prev_frame = None
    compare_frame = None
    last_compare_frame_at = None

    state = "STILL"
    state_change_at = None
    last_motion_at = None

    video = None
    video_path = None

    config.logger.info("starting recorder loop...")

    def start_video_file():
        video_path = config.MD_STORAGE_PATH + '/motion.' + datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S') + '.avi'  
        config.logger.info('writing video to %s' % video_path)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video = cv2.VideoWriter(video_path, fourcc, config.MD_MOTION_FPS, config.MD_RESOLUTION, isColor=True)
        return video, video_path

    def write_frame_to_video(video, frame):
        video.write(frame)

    def end_video(video, video_path):
        video.release()
        mp4_path = video_path.replace('.avi', '.mp4')
        config.logger.info('finished writing to video')
        os.system('ffmpeg -hide_banner -loglevel error -i %s -vcodec libx264 -movflags +faststart %s' % (video_path, mp4_path))
        config.logger.info('finished converting video to mp4 at %s' % mp4_path)
        os.remove(video_path)
        return mp4_path

    def calc_brightness(cache = {}):
        now = datetime.datetime.now(config.MD_LOCATION_INFO.tzinfo)
        
        if 'day' not in cache or cache['day'] != now.date():
            cache['day'] = now.date()
            cache['sunrise'] = astral.sun.sunrise(config.MD_LOCATION_INFO.observer, tzinfo=config.MD_LOCATION_INFO.tzinfo)
            cache['sunset'] = astral.sun.sunset(config.MD_LOCATION_INFO.observer, tzinfo=config.MD_LOCATION_INFO.tzinfo)
            config.logger.info('calculated sunrise and sunset: ' + str(cache))

        if now > cache['sunrise'] and now < cache['sunset']:
            return config.MD_DAY_BRIGHTNESS
        else:
            return config.MD_NIGHT_BRIGHTNESS

    # set initial brightness and sleep to avoid brightness flicker triggering motion detection
    if hasattr(vs.stream, 'camera'):
        vs.stream.camera.brightness = calc_brightness()
        sleep(0.5)

    while True:
        if hasattr(vs.stream, 'camera'):
            vs.stream.camera.brightness = calc_brightness()

        # grab the current frame and initialize the occupied/unoccupied
        # text
        frame = vs_stream.read()

        # if the frame could not be grabbed, then we have reached the end
        # of the video
        if frame is None:
            config.logger.error("Could not retrieve frame, ending...")
            break

        # resize the frame, convert it to grayscale, and blur it
        orig_frame = frame
        frame = imutils.resize(frame, width=config.MD_RESIZE_WIDTH)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if compare_frame is None:
            compare_frame = gray
            last_compare_frame_at = time()
            continue

        frameDelta = cv2.absdiff(compare_frame, gray)
        thresh = cv2.threshold(frameDelta, 50, 255, cv2.THRESH_BINARY)[1]

        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # loop over the contours
        detected_motion = False
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < config.MD_MIN_AREA:
                continue

            if debug:
                # compute the bounding box for the contour, draw it on the frame,
                # and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            detected_motion = True
            last_motion_at = time()

        motion_duration = time() - state_change_at if state_change_at else 0
        stillness_duration = time() - last_motion_at if last_motion_at else 0

        def end_motion():
            nonlocal state, state_change_at, compare_frame, video, video_path
            video_path = end_video(video, video_path)

            if queue is not None:
                queue.put(video_path)

            state = "STILL"
            state_change_at = time()
            video = None
            video_path = None

        # start recording
        if state == "STILL" and detected_motion:
            config.logger.info('motion started')
            state = "MOTION"
            state_change_at = time()
            video, video_path = start_video_file()
            if prev_frame is not None:
                write_frame_to_video(video, prev_frame)
            write_frame_to_video(video, orig_frame)
        # stop recording (max duration exceeded)
        elif state == "MOTION" and motion_duration > config.MD_MAX_DURATION_S:
            config.logger.info('motion stopped (max time exceeded)')
            write_frame_to_video(video, orig_frame)
            end_motion()
        # stop recording (motion stopped)
        elif state == "MOTION" and stillness_duration > config.MD_MIN_DURATION_S:
            config.logger.info('motion stopped')
            end_motion()
        # continue recording
        elif state == "MOTION":
            write_frame_to_video(video, orig_frame)

        # sleep until next frame at desired FPS
        # todo: this is not really tracking at the right fps since it does not account
        # for processing time of each frame but is good for keeping a consistent cpu usage
        # which helps with temperature management, this can be improved to calculate the time
        # until the next frame and potentially slow if temp rises beyond a threshold 
        sleep(1 / (config.MD_STILL_FPS if state == "STILL" else config.MD_MOTION_FPS))

        # keep previous frame for writing to video if motion occurs
        prev_frame = orig_frame

        # use latest motion frame to compare with next frame
        if detected_motion or time() - last_compare_frame_at > 60:
            compare_frame = gray
            last_compare_frame_at = time()

        if debug:
            # draw the text and timestamp on the frame
            cv2.putText(frame, "Room Status: {}".format(state), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            # show the frame and record if the user presses a key
            cv2.imshow("Security Feed", frame)
            cv2.imshow("Thresh", thresh)
            cv2.imshow("Frame Delta", frameDelta)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break

    # cleanup the camera and close any open windows
    vs_stream.stop()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    start_recorder(debug=True)
