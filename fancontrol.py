#!/bin/env python
"""
RPi FanControl
Copyright (C) 2024 PitcherSeven

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO


# noinspection PyMethodMayBeStatic
class FanController:
    COOLING_DURATION_MINUTES = 3

    GPIO_PIN = 18  # The GPIO_PIN ID, edit here to change it
    MAX_TEMP: float = float(45)  # The maximum temperature in Celsius after which we trigger the fan
    STOP_TEMP: float = MAX_TEMP - float(7.5)  # The maximum temperature in Celsius as lower boundary trigger turning off
    TEMP_SENSOR = "vcgencmd measure_temp"
    THRESHOLD_STABLE_SECONDS = 30

    overheat_time: datetime
    fan_start_time: datetime
    current_temp: float
    current_state: bool = False

    def setup(self) -> bool:
        """
        Sets the mode and warnings for the GPIO setup.
        :return: TRUE, if setup was successful.
        """
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(FanController.GPIO_PIN, GPIO.OUT)

            self.run_self_test()
            return True
        except Exception as e:
            print(f'[FanControl]: ERROR while setup: {e}')
            return False

    def destruct(self):
        GPIO.cleanup()  # resets all GPIO ports used by this program

    def run_self_test(self) -> None:
        try:
            self.set_fan_pin(True)
            sleep(5)
            self.set_fan_pin(False)
            sleep(1)
            print('[FanControl]: Successfully ran self test on init')
        except Exception as e:
            print(f'[FanControl]: ERROR while self-test: {e}')

    def get_cpu_temperature(self) -> float:
        """
        Retrieves the CPU temperature of the Raspberry Pi using vcgencmd.
        :return: A float value which indicates the CPU temperature.
        """
        with (os.popen(FanController.TEMP_SENSOR) as f):
            cpu_temp_formatted = f.readline()
        if "=" not in cpu_temp_formatted:
            raise Exception("[FanControl] ERROR: Expected formatted output \"Temp=[value float]'C\"")
        if "'" not in cpu_temp_formatted:
            raise Exception("[FanControl] ERROR: Expected formatted output \"Temp=[value float]'C\"")
        temp_part = cpu_temp_formatted.split('=')[1].split('\'')[0]
        self.current_temp = float(temp_part)
        return self.current_temp

    def fan_on(self) -> None:
        """
        Turns the fan on by setting the GPIO GPIO_PIN mode.
        """
        if self.current_state:
            return  # No need to enable twice

        seconds_diff = (datetime.now() - self.overheat_time).total_seconds()
        if seconds_diff < FanController.THRESHOLD_STABLE_SECONDS:
            return

        # Here we know that temp was too high
        print(f'[FanControl] WARN: Threshold of {FanController.MAX_TEMP}°C'
              f'reached ({self.current_temp}°C) - turning on fan')
        self.set_fan_pin(True)

    def fan_off(self) -> None:
        """
        Turns the fan off by setting the GPIO GPIO_PIN mode.
        """
        if not self.current_state:
            return  # No need to disable twice

        minutes_diff = (datetime.now() - self.fan_start_time).total_seconds() / float(60.0)
        if minutes_diff < FanController.COOLING_DURATION_MINUTES:
            return

        print(f'[FanControl]: STOP fan after {FanController.COOLING_DURATION_MINUTES}min,'
              f'started at {self.overheat_time:%Y-%m-%d %H:%M:%S}')
        self.set_fan_pin(False)

    def run(self) -> None:
        """
        Retrieves the CPU temperature of the Raspberry Pi and turns the fan
        on or off based on the read value.
        """
        cpu_temp = float(self.get_cpu_temperature())
        if cpu_temp > FanController.MAX_TEMP:
            self.overheat_time = datetime.now()
            self.fan_on()
        elif cpu_temp < FanController.STOP_TEMP:
            self.overheat_time = datetime(3000, 1, 1)
            self.fan_off()

    def set_fan_pin(self, mode: bool) -> None:
        """
        Sets the GPIO GPIO_PIN to the mode needed depending on the CPU temperature.
        :param mode: A boolean, True or False.
        """
        self.current_state = mode
        GPIO.output(FanController.GPIO_PIN, mode)
        if mode:
            self.fan_start_time = datetime.now()
