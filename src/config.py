import logging
import os

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

class State:
    ALIVE = 1
    TERMINATING = 2
    UPDATING = 3

class Config:
    # Motion Detection (MD) config
    MD_MIN_AREA = 500
    MD_RESIZE_WIDTH = 240
    MD_RESOLUTION = (640, 480)
    MD_MIN_DURATION_S = 5
    MD_MAX_DURATION_S = 60
    MD_STILL_FPS = 1
    MD_MOTION_FPS = 10
    MD_STORAGE_PATH = "data/video"
    MD_STORAGE_MAX_AGE = 30 * 24 * 3600

    # Auto Updater (AD) config
    AD_INTERVAL_S = 5 * 60

    def __init__(self):
        self.logger = logging.getLogger('smartpetdoor')

        self.init_paths()

    def init_paths(self):
        os.makedirs(self.MD_STORAGE_PATH, exist_ok=True)

config = Config()
