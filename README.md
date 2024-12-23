# RPi-FanControl
A Python programm, that reads the core termperature using `vcgencmd measure_temp` and controls a fan based on output.

## Pre-conditions
In order to control the fan using one GPIO pin, you'll need to setup a circuit accordingly, this project is not about.
<br/>The origin setup was a GPIO pin connected to a NPN S8050 transistor controlling the power circuit of the fan connected.
<br/>You'll find many tutorials or pages, describing the usage of transistors, to control things using GPIO.
<br/>

## Manual use
A path can be defined, where the user can echo `1` or `0` in order to control the fan manually.
<br/>This will override the temperature related fan control, if set `1`, `0` basically has no effect yet.
<br/>

## Configuration
The interesting parts to configure are following constants:

### LOOP_SECONDS (main.py)
The time, Python should sleep between iterations. Default: 5 seconds
<br/>

### MAX_TEMP (fancontrol.py)
Temperature in °C, the fan will be started by. Default: 45°C
<br/>

### STOP_TEMP (fancontrol.py)
Lower temperature threshold in °C, the fan will be stopped. Default: 45°C - 7.5°C
<br/>

### THRESHOLD_STABLE_SECONDS (fancontrol.py)
Duration the must be stable for, before starting the fan. Default: 30 seconds
<br/>

### COOLING_DURATION_MINUTES (fancontrol.py)
Duration the fan should run in any case, after being started once. Default: 3 minutes
<br/>
