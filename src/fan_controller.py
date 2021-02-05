from time import sleep
import subprocess
import os
import sys
from sys import platform

from gpiozero import Device, PWMOutputDevice, OutputDevice

from .config import config, TempRange

# Basic fan control using a GPIO pin (requires external circuitry)
# see https://www.instructables.com/PWM-Regulated-Fan-Based-on-CPU-Temperature-for-Ras/


def fan_controller(shared):

    fan_pin = get_fan_controller_pin()
    fan_speed = 0.0
    sleep(1)

    try:
        while True:
            if 'temp' in shared and 'c' in shared['temp']:
                temp = shared['temp']['c']
                if temp < config.FC_FAN_MIN_TEMP:
                    fan_speed = 0.0
                elif temp > config.FC_FAN_MAX_TEMP:
                    fan_speed = config.FC_PWM_MAX_VAL
                else:
                    fan_speed = config.FC_PWM_MIN_VAL + (
                        (config.FC_PWM_MAX_VAL - config.FC_PWM_MIN_VAL)
                        * (temp - config.FC_FAN_MIN_TEMP) / (config.FC_FAN_MAX_TEMP - config.FC_FAN_MIN_TEMP)
                        )

            config.logger.info('setting fan speed to %.2f' % fan_speed)
            fan_pin.value = fan_speed

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

    return PWMOutputDevice(pin=config.FC_GPIO_PIN, frequency=config.FC_PWM_FREQ_HZ, pin_factory=pin_factory)


if __name__ == '__main__':
    fan_controller({'temp': {'c': 75}})
