from .config import config, TempRange

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

def start_recorder(queue = None, shared = {}, debug = False):
    vs = VideoStream(src=0, resolution=config.MD_RESOLUTION, usePiCamera='linux' in platform)
    vs_stream = vs.start()

    sleep(3.0)

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
        config.logger.info('finished writing to video')
        
    def is_day(cache = {}):
        now = datetime.datetime.now(config.MD_LOCATION_INFO.tzinfo)
        
        if 'day' not in cache or cache['day'] != now.date():
            cache['day'] = now.date()
            cache['sunrise'] = astral.sun.sunrise(config.MD_LOCATION_INFO.observer, tzinfo=config.MD_LOCATION_INFO.tzinfo)
            cache['sunset'] = astral.sun.sunset(config.MD_LOCATION_INFO.observer, tzinfo=config.MD_LOCATION_INFO.tzinfo)
            config.logger.info('calculated sunrise and sunset: ' + str(cache))

        return now > cache['sunrise'] and now < cache['sunset']

    def calc_brightness():
        if is_day():
            return config.MD_DAY_BRIGHTNESS
        else:
            return config.MD_NIGHT_BRIGHTNESS

    def get_pixel_change_threshold():
        if is_day():
            return config.MD_DAY_PIXEL_CHANGE_THRESHOLD
        else:
            return config.MD_NIGHT_PIXEL_CHANGE_THRESHOLD

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
        frame = imutils.resize(frame, width=config.MD_RESIZE_WIDTH, inter=cv2.INTER_NEAREST)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if compare_frame is None:
            compare_frame = gray
            last_compare_frame_at = time()
            continue

        frameDelta = cv2.absdiff(compare_frame, gray)
        thresh = cv2.threshold(frameDelta, get_pixel_change_threshold(), 255, cv2.THRESH_BINARY)[1]

        # calculate portion of pixels that changed
        amount_changed = np.count_nonzero(thresh) / thresh.size
        detected_motion = amount_changed > config.MD_IMAGE_CHANGE_THRESHOLD

        # sleep until next frame at desired FPS
        # todo: this is not really tracking at the right fps since it does not account
        # for processing time of each frame but is good for keeping a consistent cpu usage
        # which helps with temperature management, this can be improved to calculate the time
        # until the next frame and potentially slow if temp rises beyond a threshold 
        def sleep_interval(state):
            nonlocal shared

            base_interval = 1 / (config.MD_STILL_FPS if state == "STILL" else config.MD_MOTION_FPS)

            if 'temp' in shared and 'range' in shared['temp']:
                r = shared['temp']['range']
                if r == TempRange.HOT:
                    base_interval *= 2
                elif r == TempRange.VERY_HOT:
                    base_interval *= 8
                elif r == TempRange.DANGEROUS:
                    config.logger.info('cpu is dangerously hot, sleeping for 60s')
                    base_interval = 60
            
            return base_interval


        if detected_motion:
            last_motion_at = time()

        motion_duration = time() - state_change_at if state_change_at else 0
        stillness_duration = time() - last_motion_at if last_motion_at else 0

        def end_motion():
            nonlocal state, state_change_at, compare_frame, video, video_path
            end_video(video, video_path)

            if queue is not None:
                queue.put({'type': 'motion', 'path': video_path})

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

        sleep(sleep_interval(state))

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
    print('pid: ', os.getpid())
    start_recorder(debug=True)
