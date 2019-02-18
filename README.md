# pyShelly

Library for Shelly smart home devices

## Features:
- Discover devices
- Monitor status
- Control (turn on/off etc)

## Devices supported:
- Shelly 1
- Shelly 2 (relay or roller mode)
- Shelly 4
- Shelly PLUG
- Shelly BULB (only on/off and dim)
- Shelly RGBWW (only on/off and dim)
- Shelly H&T

## Device support comming soon:
- Shelly RGBW2
- Shelly 2.5
- Shelly PLUG S

## Usage:
```python
shelly = pyShelly()
shelly.cb_deviceAdded = deviceAdded
shelly.open()
shelly.discover()

def deviceAdded(dev):
  print (dev.devType)
```
