import os
import subprocess
import math
import tensorflow as tf
from .model import INPUT_SHAPE
from ..config import config

MAX_FRAMES = INPUT_SHAPE[0]
FRAME_WIDTH = INPUT_SHAPE[1]
FRAME_HEIGHT = INPUT_SHAPE[2]
MIN_FRAME_INTERVAL = config.MD_MOTION_FPS

def preprocess_video(video_path: str):
    frames = get_frame_count(video_path)
    
    frame_interval = max(MIN_FRAME_INTERVAL, 0 if frames <= MAX_FRAMES else math.floor(frames / MAX_FRAMES))

    frames_buffer = read_frames(video_path, frame_interval, (FRAME_WIDTH, FRAME_HEIGHT))

    frames_tensor = tf.io.decode_raw(frames_buffer, out_type='uint8')
    
    if len(frames_buffer) > MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT:
        frames_tensor = frames_tensor[:MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT]
    elif len(frames_buffer) < MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT:
        padding = MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT - len(frames_buffer)
        frames_tensor = tf.pad(frames_tensor, tf.constant([[0, padding]]))

    frames_tensor = tf.reshape(frames_tensor, INPUT_SHAPE)

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
    frames = preprocess_video('/Users/elliotlevin/Temp/motion/motion.2021-01-29T08-59-15.mp4')
    print(frames)
