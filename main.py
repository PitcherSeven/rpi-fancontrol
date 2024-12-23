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
from fancontrol import FanController

# Interval duration, the fan control is triggered
LOOP_SECONDS = 5
# File where user could manually start fan
OVERRIDE_FILE = "/opt/fancontrol/manual"
# Determines, if user started fan
userMode: bool = False


def override_thresholds() -> bool:
    try:
        if not os.path.exists(OVERRIDE_FILE):
            return False
        with (open(OVERRIDE_FILE, 'r') as f):
            override_val = f.readline()

        int_val = int(override_val)
        return bool(int_val)
    except Exception as e:
        print(e)
    return False


print(f'[FanControl]: Starting {FanController.__name__}...')
controller = FanController()
try:
    controller.setup()
    while True:
        is_user_mode = override_thresholds()
        if is_user_mode and userMode:
            sleep(LOOP_SECONDS)
            continue
        if is_user_mode:
            print('[FanControl]: User requested manual starting fan')
            controller.set_fan_pin( True)
        else:
            controller.run()
        sleep(LOOP_SECONDS)
finally:
    controller.destruct()
