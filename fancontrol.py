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


def destruct():
    # resets all GPIO ports used by this program
    GPIO.cleanup()


class FanController:
    # Minutes duration, the fan will be active for, after being started
    COOLING_DURATION_MINUTES = 3

    # GPIO_PIN controlling the fan
    GPIO_PIN = 18

    # Maximum temperature in °C, the fan will be activated at
    MAX_TEMP: float = float(45)

    # Lower temperature threshold, where the fan could be stopped
    STOP_TEMP: float = MAX_TEMP - float(7.5)

    # Sensor, that returns the temperature
    TEMP_SENSOR = "vcgencmd measure_temp"

    # Seconds that must be passed, to determine overheat
    THRESHOLD_STABLE_SECONDS = 30

    # Timestamp of last overheat detection of future (OFF)
    overheat_time: datetime = datetime(3000, 1, 1)
    # Timestamp, where fan was started
    fan_start_time: datetime
    # Current temperature
    current_temp: float
    # Current fan state
    current_state: bool = False

    def setup(self) -> bool:
        """
        Sets the mode ignores warnings for GPIO
        and starts the fan for 5sec
        :return: bool indicating if setup was successfully or not
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

    def run_self_test(self) -> None:
        """
        Starts the fan for 5 seconds
        :return: None
        """
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
        Retrieves the CPU temperature using vcgencmd.
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

    def start_fan(self) -> None:
        """
        Starts the fan, if required and not yet started
        :return: None
        """
        if self.current_state:
            return  # No need to enable twice

        seconds_diff = (datetime.now() - self.overheat_time).total_seconds()
        if seconds_diff < FanController.THRESHOLD_STABLE_SECONDS:
            print(f'[FanControl] WARN: Threshold of {FanController.MAX_TEMP}°C reached ({self.current_temp}°C) '
                  '- waiting to stabilize.')
            return

        # Here we know that temp was too high
        print(f'[FanControl] WARN: Threshold of {FanController.MAX_TEMP}°C reached ({self.current_temp}°C) - turning on fan')
        self.set_fan_pin(True)

    def stop_fan(self) -> None:
        """
        Stops the fan, if required and not yet stopped
        :return: None
        """
        if not self.current_state:
            return  # No need to disable twice

        minutes_diff = (datetime.now() - self.fan_start_time).total_seconds() / float(60.0)
        if minutes_diff < FanController.COOLING_DURATION_MINUTES:
            return

        print(f'[FanControl]: STOP fan after {FanController.COOLING_DURATION_MINUTES}min,'
              f'started at {self.fan_start_time:%Y-%m-%d %H:%M:%S}')
        print(f'[FanControl]: current temperature: {self.current_temp}°C')
        self.set_fan_pin(False)

    def run(self) -> None:
        """
        Run routine for public use.
        Receives the core temp and starts/stops accordingly
        :return: None
        """
        cpu_temp = float(self.get_cpu_temperature())
        if cpu_temp > FanController.MAX_TEMP:
            if self.overheat_time.year == 3000:
                self.overheat_time = datetime.now()
            self.start_fan()
        elif cpu_temp < FanController.STOP_TEMP:
            self.stop_fan()
            self.overheat_time = datetime(3000, 1, 1)

    def set_fan_pin(self, mode: bool) -> None:
        """
        Sets the configured GPIO pin for controlling the fan
        :param mode:
        :return:
        """
        self.current_state = mode
        GPIO.output(FanController.GPIO_PIN, mode)
        if mode:
            self.fan_start_time = datetime.now()
