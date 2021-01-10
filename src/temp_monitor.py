from time import sleep
import subprocess
import os
import sys

from config import config, TempRange
from sys import platform

def temp_monitor(shared):
   while True:
        temp_c = get_temp()
        temp_range = calc_range(temp_c)

        shared['temp'] = {
            'c': temp_c,
            'range': temp_range
        }

        sleep(float(config.TM_MEASURE_INTERVAL_S)) 

def get_temp():
    config.logger.info('checking cpu temp...')
    if 'linux' in platform:
        temp = float(open('/sys/class/thermal/thermal_zone0/temp', 'r').read()) / 1000
    else:
        config.logger.info('cannot determine temp on %s platform (will use 60)' % platform)
        temp = 60.

    config.logger.info('cpu temp: %d' % temp)

    return temp

def calc_range(temp):
    temp_range = TempRange.COOL
    
    for range1, threshold in reversed(list(config.TM_THRESHOLDS_C.items())):
        if temp >= float(threshold):
            temp_range = range1
            break

    config.logger.info('temp range is %s' % TempRange.name(temp_range))
    return temp_range

if __name__ == '__main__':
    temp_monitor({})