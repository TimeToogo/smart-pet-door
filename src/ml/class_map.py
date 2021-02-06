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

def create_class_map():
    # creates mapping from model output prediction to [pet class, event class] as per ../config.py

    class_map = {}

    i = 0
    for pet_class in config.VC_PET_CLASSES.values():
        for event_class in config.VC_EVENT_CLASSES.values():
            class_map[i] = (pet_class, event_class)
            i += 1

    class_map[i] = 'DISCARD'
    i += 1

    reverse_class_map = {}

    for model_class, config_classes in class_map.items():
        if config_classes == 'DISCARD':
            reverse_class_map['DISCARD'] = model_class
        else:
            reverse_class_map['_'.join(map(str, config_classes))] = model_class

    return class_map, reverse_class_map

class_map, reverse_class_map = create_class_map()
