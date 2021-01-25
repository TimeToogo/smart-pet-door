import logging
import os
from astral.geocoder import lookup, database

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

class State:
    ALIVE = 1
    TERMINATING = 2
    UPDATING = 3

class TempRange:
    COOL = 1
    HOT = 2
    VERY_HOT = 3
    DANGEROUS = 4

    @staticmethod
    def name(temp_range: int) -> str:
        return ['COOL', 'HOT', 'VERY_HOT', 'DANGEROUS'][temp_range - 1]

class Config:
    # Motion Detection (MD) config
    MD_MIN_AREA = 100
    MD_RESIZE_WIDTH = 240
    MD_RESOLUTION = (640, 480)
    MD_MIN_DURATION_S = 5
    MD_MAX_DURATION_S = 60
    MD_STILL_FPS = 1
    MD_MOTION_FPS = 10
    MD_STORAGE_PATH = "data/video"
    MD_STORAGE_MAX_AGE = 30 * 24 * 3600
    MD_DAY_BRIGHTNESS = 50
    MD_NIGHT_BRIGHTNESS = 65
    MD_LOCATION_INFO = lookup("Melbourne", database())

    # Auto Updater (AD) config
    AD_INTERVAL_S = 5 * 60

    # Temp monitor (TM) config
    TM_MEASURE_INTERVAL_S = 15
    TM_THRESHOLDS_C = {
        TempRange.HOT: 60,
        TempRange.VERY_HOT: 70,
        TempRange.DANGEROUS: 80
    }

    ## Fan Controller (FC) config
    FC_GPIO_PIN = 16
    FC_FAN_ON_THRESHOLD = TempRange.HOT
    FC_UPDATE_INTERVAL_S = 15

    # API
    API_BIND = "0.0.0.0:8080"


    def __init__(self):
        self.logger = logging.getLogger('smartpetdoor')

        self.init_paths()

    def init_paths(self):
        os.makedirs(self.MD_STORAGE_PATH, exist_ok=True)

config = Config()
