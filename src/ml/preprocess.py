import os
import sys
import subprocess
import math
import numpy as np
from ..config import config

MAX_FRAMES = config.VC_INPUT_SHAPE[0]
FRAME_WIDTH = config.VC_INPUT_SHAPE[1]
FRAME_HEIGHT = config.VC_INPUT_SHAPE[2]
MIN_FRAME_INTERVAL = math.floor(config.MD_MOTION_FPS / 3) # extract at most ~3 fps

def preprocess_video(video_path: str):
    frames = get_frame_count(video_path)
    
    frame_interval = max(MIN_FRAME_INTERVAL, 0 if frames <= MAX_FRAMES else math.floor(frames / MAX_FRAMES))

    frames_buffer = read_frames(video_path, frame_interval, (FRAME_WIDTH, FRAME_HEIGHT))

    frames_tensor = np.frombuffer(frames_buffer, dtype='uint8').astype('float32')
    frames_tensor = frames_tensor / 255
 
    if len(frames_buffer) > MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT:
        frames_tensor = frames_tensor[:MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT]
    elif len(frames_buffer) < MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT:
        padding = MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT - len(frames_buffer)
        frames_tensor = np.pad(frames_tensor, (0, padding))

    frames_tensor = np.reshape(frames_tensor, config.VC_INPUT_SHAPE)

    return frames_tensor

def get_frame_count(video_path: str) -> int:
    proc = subprocess.run([
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'v:0',
            '-show_entries',
            'stream=nb_frames',
            '-print_format',
            'default=nokey=1:noprint_wrappers=1',
            video_path
        ],
        stdout=subprocess.PIPE
    )

    return int(proc.stdout.decode('utf8'))

def read_frames(video_path: str, frame_interval: int, frame_dims) -> bytes:
    proc = subprocess.run([
            'ffmpeg',
            '-v',
            'error',
            '-i',
            video_path,
            '-vf',
            'scale=%d:%d,select=not(mod(n\,%d))' % (frame_dims + (frame_interval,)),
            '-vsync',
            'vfr',
            '-f',
            'image2pipe',
            '-vcodec',
            'rawvideo',
            '-pix_fmt',
            'gray8',
            '-',
        ],
        stdout=subprocess.PIPE
    )

    return proc.stdout

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    frames = preprocess_video(sys.argv[1])
    plt.imshow(frames.reshape(MAX_FRAMES * FRAME_HEIGHT, FRAME_WIDTH, 1))
    plt.show()
    print(frames, frames.shape)
