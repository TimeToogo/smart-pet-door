from config import config

from imutils.video import VideoStream
import datetime
import imutils
from time import sleep, time
import cv2
import numpy as np
import os

vs = VideoStream(src=0, resolution=config.MD_RESOLUTION).start()
sleep(2.0)

prev_frame = None
compare_frame = None
compare_frate_time = None

state = "STILL"
state_change_at = None
last_motion_at = None

config.logger.info("Starting recorder loop...")

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
    os.system('ffmpeg -hide_banner -loglevel error -i %s -vcodec libx264 %s' % (video_path, mp4_path))
    config.logger.info('finished converting video to mp4 at %s' % mp4_path)
    os.remove(video_path)

# loop over the frames of the video
while True:
    # grab the current frame and initialize the occupied/unoccupied
    # text
    frame = vs.read()
    frame = frame

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
        compare_frate_time = time()
        continue

    frameDelta = cv2.absdiff(compare_frame, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

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

        if config.MD_DEBUG:
            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        detected_motion = True
        last_motion_at = time()

    motion_duration = time() - state_change_at if state_change_at else 0
    stillness_duration = time() - last_motion_at if last_motion_at else 0

    def end_motion():
        global state, state_change_at, compare_frame, compare_frate_time, video
        state = "STILL"
        state_change_at = time()
        compare_frame = gray
        compare_frate_time = time()
        video = None

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
        end_video(video, video_path)
        end_motion()
    # stop recording (motion stopped)
    elif state == "MOTION" and stillness_duration > config.MD_MIN_DURATION_S:
        config.logger.info('motion stopped')
        end_video(video, video_path)
        end_motion()
    # continue recording
    elif state == "MOTION":
        write_frame_to_video(video, orig_frame)

    # sleep until next frame at desired FPS
    sleep(1 / (config.MD_STILL_FPS if state == "STILL" else config.MD_MOTION_FPS))
    prev_frame = orig_frame

    if config.MD_DEBUG:
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
vs.stop()
cv2.destroyAllWindows()