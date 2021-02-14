from .config import config

from .lib.amg8833_i2c import AMG8833
import datetime
import pytz
import imutils
from time import sleep, time
import cv2
import numpy as np
import os
import astral.sun
from sys import platform

def start_thermal_recorder(queue = None, shared = {}, debug = False):

    thermal_cam = AMG8833(addr=config.TC_ADDR)

    sleep(3.0)

    prev_frame = None
    compare_frame = None
    last_compare_frame_at = None

    state = "STILL"
    state_change_at = None
    last_motion_at = None

    video = None
    video_path = None

    config.logger.info("starting thermal camera loop...")
    os.makedirs(config.TC_STORAGE_PATH, exist_ok=True)

    def start_video_file():
        video_path = config.TC_STORAGE_PATH + '/thermal.' + datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S') + '.avi'  
        config.logger.info('writing video to %s' % video_path)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video = cv2.VideoWriter(video_path, fourcc, config.TC_MOTION_FPS, config.TC_RESOLUTION, isColor=False)
        return video, video_path

    def write_frame_to_video(video, frame):
        video.write(frame)

    def end_video(video, video_path):
        video.release()
        config.logger.info('finished writing to video')

    def normalise_frame(frame):
        # clip to min-max values
        frame = np.clip(frame, config.TC_MIN_TEMP_C, config.TC_MAX_TEMP_C)
        # normalise to 0-255 range
        frame = (frame - config.TC_MIN_TEMP_C) / (config.TC_MAX_TEMP_C - config.TC_MIN_TEMP_C)
        frame = frame.astype('uint8')

        return frame

    while True:
        error, frame = thermal_cam.read_temp()

        # if the frame could not be grabbed, then we have reached the end
        # of the video
        if error:
            config.logger.error("Could not retrieve frame, ending...")
            break

        temp_frame = frame
        frame = normalise_frame(frame)

        if compare_frame is None:
            compare_frame = temp_frame
            last_compare_frame_at = time()
            continue

        frameDelta = cv2.absdiff(compare_frame, temp_frame)
        thresh = cv2.threshold(frameDelta, config.TC_CHANGE_TEMP_PIXEL_THRESHOLD, config.TC_MAX_TEMP_C, cv2.THRESH_BINARY)[1]

        # calculate portion of pixels that changed
        detected_motion = np.count_nonzero(thresh) > config.TC_CHANGE_TEMP_IMAGE_THRESHOLD_PIXELS

        if detected_motion:
            last_motion_at = time()

        motion_duration = time() - state_change_at if state_change_at else 0
        stillness_duration = time() - last_motion_at if last_motion_at else 0

        def end_motion():
            nonlocal state, state_change_at, compare_frame, video, video_path
            end_video(video, video_path)

            if queue is not None:
                queue.put({'type': 'thermal', 'path': video_path})

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
            write_frame_to_video(video, frame)
        # stop recording (max duration exceeded)
        elif state == "MOTION" and motion_duration > config.TC_MAX_DURATION_S:
            config.logger.info('motion stopped (max time exceeded)')
            write_frame_to_video(video, frame)
            end_motion()
        # stop recording (motion stopped)
        elif state == "MOTION" and stillness_duration > config.TC_MIN_DURATION_S:
            config.logger.info('motion stopped')
            end_motion()
        # continue recording
        elif state == "MOTION":
            write_frame_to_video(video, frame)

        sleep_interval = 1 / (config.TC_STILL_FPS if state == "STILL" else config.TC_MOTION_FPS)
        sleep(sleep_interval)

        # keep previous frame for writing to video if motion occurs
        prev_frame = frame

        # use latest motion frame to compare with next frame
        if detected_motion or time() - last_compare_frame_at > 60:
            compare_frame = temp_frame
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
    cv2.destroyAllWindows()

if __name__ == '__main__':
    print('pid: ', os.getpid())
    start_thermal_recorder(debug=True)
