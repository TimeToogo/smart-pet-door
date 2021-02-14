import os
import sys
import subprocess
import math
import numpy as np
from ..config import config

MAX_FRAMES = config.VC_INPUT_SHAPE[0]
FRAME_HEIGHT = config.VC_INPUT_SHAPE[1]
FRAME_WIDTH = config.VC_INPUT_SHAPE[2]
CHANNELS = config.VC_INPUT_SHAPE[3]
MIN_FRAME_INTERVAL = math.floor(config.MD_MOTION_FPS / 3) # extract at most ~3 fps

def preprocess_video(video_path: str, cache=False, ffmpeg_threads=None):
    cache_file = get_cache_file_path(video_path)

    if cache and os.path.isfile(cache_file):
        with open(cache_file, 'rb') as file:
            cached_tensor = np.frombuffer(file.read(), dtype='float32')
            return np.reshape(cached_tensor, config.VC_INPUT_SHAPE)

    frames = get_frame_count(video_path, ffmpeg_threads)
    
    frame_interval = max(MIN_FRAME_INTERVAL, 0 if frames <= MAX_FRAMES else math.floor(frames / MAX_FRAMES))

    frames_buffer = read_frames(video_path, frame_interval, (FRAME_WIDTH, FRAME_HEIGHT), ffmpeg_threads)

    frames_tensor = np.frombuffer(frames_buffer, dtype='uint8').astype('float32')
    frames_tensor = frames_tensor / 255

    max_length = MAX_FRAMES * FRAME_WIDTH * FRAME_HEIGHT * CHANNELS
 
    if len(frames_buffer) > max_length:
        frames_tensor = frames_tensor[:max_length]
    elif len(frames_buffer) < max_length:
        padding = max_length - len(frames_buffer)
        frames_tensor = np.pad(frames_tensor, (0, padding))

    frames_tensor = np.reshape(frames_tensor, config.VC_INPUT_SHAPE)

    if cache:
        os.makedirs(config.VC_PREPROCESS_CACHE_PATH, exist_ok=True)
        with open(cache_file, 'wb') as file:
            file.write(frames_tensor.tobytes())

    return frames_tensor

def get_cache_file_path(video_path: str) -> str:
    file_name = os.path.basename(video_path)

    return os.path.realpath(config.VC_PREPROCESS_CACHE_PATH + '/preprocessed-' + file_name + '.tensor')

def get_frame_count(video_path: str, threads) -> int:
    proc = subprocess.run([
            'ffprobe',
            '-v',
            'error',
            '-threads',
            str(threads) if threads else 'auto',
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

def read_frames(video_path: str, frame_interval: int, frame_dims, threads) -> bytes:
    proc = subprocess.run([
            'ffmpeg',
            '-v',
            'error',
            '-threads',
            str(threads) if threads else 'auto',
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
            'rgb24',
            '-',
        ],
        stdout=subprocess.PIPE
    )

    return proc.stdout

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    frames = preprocess_video(sys.argv[1], cache=True, ffmpeg_threads=1)
    plt.imshow(frames.reshape(MAX_FRAMES * FRAME_HEIGHT, FRAME_WIDTH, CHANNELS))
    plt.show()
    print(frames, frames.shape)
