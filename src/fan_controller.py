from time import sleep
import subprocess
import os
import sys

from gpiozero import Device, OutputDevice

from config import config, TempRange
from sys import platform

# Basic fan control using a GPIO pin (requires external circuitry)
# see https://www.instructables.com/PWM-Regulated-Fan-Based-on-CPU-Temperature-for-Ras/ (this without pwm)
def fan_controller(shared):

    fan_pin = get_fan_controller_pin()
    current_state = False

    try:
        while True:
            if 'temp' in shared and 'range' in shared['temp']:
                r = shared['temp']['range']
                current_state = r >= config.FC_FAN_ON_THRESHOLD

            if current_state != fan_pin.is_active:
                if current_state:
                    config.logger.info('cpu temp is above threshold, turning fan on')
                    fan_pin.on()
                else:
                    config.logger.info('cpu temp is below threshold, turning fan pin off')
                    fan_pin.off()

            sleep(config.FC_UPDATE_INTERVAL_S)
    finally:
        fan_pin.close()

def get_fan_controller_pin():
    pin_factory = None

    if 'linux' not in platform:
        from gpiozero.pins.mock import MockFactory
        config.logger.info('not running on pi, will use mock gpio pins')
        pin_factory = MockFactory()
        
    return OutputDevice(pin=config.FC_GPIO_PIN, pin_factory=pin_factory)

if __name__ == '__main__':
    fan_controller({'temp': {'range': TempRange.HOT}})
