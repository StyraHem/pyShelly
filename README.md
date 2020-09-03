[![founder-wip](https://img.shields.io/badge/founder-Håkan_Åkerberg@StyraHem.se-green.svg?style=for-the-badge)](https://www.styrahem.se)
[![buy me a coffee](https://img.shields.io/badge/If%20you%20like%20it-Buy%20me%20a%20coffee-orange.svg?style=for-the-badge)](https://www.buymeacoffee.com/styrahem)

![stability-wip](https://img.shields.io/badge/stability-stable-green.svg?style=for-the-badge)
![PyPI](https://img.shields.io/pypi/v/pyShelly.svg?color=green&style=for-the-badge)

# pyShelly

Library for Shelly smart home devices. Using CoAP for auto discovery and status updates.

This library was created for Shelly Plugins for Home Assistant and Telldus Tellstick Net/zNet v2.

## Features

- Discover devices
- Monitor status
- Monitor switch status
- Control (turn on/off etc)
- Run only locally
- Support user name and password
- Coexist with Shelly Cloud and Shelly app
- Support static and dynamic ip address
- mDns and MQTT discovery
- Cloud support (Get names of devices etc)

## Devices supported

- Shelly 1
- Shelly 1 PM (bug in firmware)
- Shelly Addon for 1/1PM, temp and humidity
- Shelly 2 (relay or roller mode)
- Shelly 4 Pro
- Shelly PLUG
- Shelly PLUG S
- Shelly BULB
- Shelly RGBWW
- Shelly RGBW2
- Shelly H&T
- Shelly EM
- Shelly 2.5 (relay or roller mode)
- Shelly 2LED
- Shelly Flood
- Shelly Door/Window
- Shelly Door/Window 2
- Shelly Dimmer
- Shelly Dimmer 2
- Shelly EM
- Shelly 3EM
- Shelly DUO
- Shelly Vintage
- Shelly i3
- Shelly Button 1
- Shelly Gas
- Shelly Air (not tested)

## Usage

```python
from pyShelly import pyShelly

def device_added(dev,code):
  print (dev," ",code)

shelly = pyShelly()
print("version:",shelly.version())

shelly.cb_device_added.append(device_added)
shelly.start()
shelly.discover()

while True:
    pass 
```

## Feedback

Please give us feedback on info@styrahem.se or Facebook groups: [Shelly grupp (Swedish)](https://www.facebook.com/groups/ShellySweden) or [Shelly support group (English)](https://www.facebook.com/groups/ShellyIoTCommunitySupport/)

## Founder

This plugin is created by the StyraHem.se, the Swedish distributor of Shelly. In Sweden you can bye Shellies from [StyraHem.se](https://www.styrahem.se/c/126/shelly) or any of the retailers like Kjell&Company, m.nu.

[![buy me a coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/styrahem)
