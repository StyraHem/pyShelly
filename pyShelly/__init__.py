# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except

import base64
from datetime import datetime, timedelta
import json
import logging
import socket
import struct
import sys
import threading
import traceback

_LOGGER = logging.getLogger('pyShelly')

NAME = "pyShelly"

__version__ = "0.1.4"
VERSION = __version__

try:
    import http.client as httplib
except:
    import httplib

if sys.version_info < (3,):
    def ba2c(x):  # Convert bytearra to compatible string
        return str(x)

    def b(x):
        return bytearray(x)

    def s(x):
        return str(x)
else:
    def ba2c(x):  # Convert bytearra to compatible bytearray
        return x

    def b(x):
        return x

    def s(x):
        return str(x, 'cp1252')

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

STATUS_RESPONSE_RELAYS = 'relays'
STATUS_RESPONSE_RELAY_OVER_POWER = 'overpower'

SENSOR_UNAVAILABLE_SEC = 3600 * 13

INFO_VALUE_RSSI = 'rssi'
INFO_VALUE_UPTIME = 'uptime'
INFO_VALUE_OVER_POWER = 'over_power'
INFO_VALUE_DEVICE_TEMP = 'device_temp'
INFO_VALUE_OVER_TEMPERATURE = 'over_temp'
INFO_VALUE_SSID = 'ssid'
INFO_VALUE_HAS_FIRMWARE_UPDATE = 'has_firmware_update'
INFO_VALUE_LATEST_FIRMWARE_VERSION = 'latest_fw_version'
INFO_VALUE_FW_VERSION = 'firmware_version'
INFO_VALUE_CLOUD_STATUS = 'cloud_status'
INFO_VALUE_CLOUD_ENABLED = 'cloud_enabled'
INFO_VALUE_CLOUD_CONNECTED = 'cloud_connected'
INFO_VALUE_MQTT_CONNECTED = 'mqtt_connected'
INFO_VALUE_CONSUMPTION = 'consumption'
INFO_VALUE_SWITCH = 'switch'
INFO_VALUE_BATTERY = 'battery'

ATTR_PATH = 'path'
ATTR_FMT = 'fmt'

BLOCK_INFO_VALUES = {
    INFO_VALUE_SSID : {ATTR_PATH :'wifi_sta/ssid'},
    INFO_VALUE_RSSI : {ATTR_PATH : 'wifi_sta/rssi'},
    INFO_VALUE_UPTIME : {ATTR_PATH : 'uptime' },
    INFO_VALUE_DEVICE_TEMP : {ATTR_PATH : 'temperature',  ATTR_FMT : 'round'},
    INFO_VALUE_OVER_TEMPERATURE : {ATTR_PATH : 'overtemperature' },
    INFO_VALUE_HAS_FIRMWARE_UPDATE : {ATTR_PATH : 'update/has_update' },
    INFO_VALUE_LATEST_FIRMWARE_VERSION : {ATTR_PATH : 'update/new_version' },   
    INFO_VALUE_FW_VERSION : {ATTR_PATH : 'update/old_version' },
    INFO_VALUE_CLOUD_ENABLED : {ATTR_PATH : 'cloud/enabled' },
    INFO_VALUE_CLOUD_CONNECTED : {ATTR_PATH : 'cloud/connected' },
    #INFO_VALUE_CLOUD_STATUS : {ATTR_PATH : 'cloud/connected' },
    INFO_VALUE_MQTT_CONNECTED : {ATTR_PATH : 'mqtt/connected' },
    INFO_VALUE_CONSUMPTION : {ATTR_PATH : 'consumption' },
    INFO_VALUE_BATTERY : {ATTR_PATH : 'bat/value' },
}

SHELLY_TYPES = {
    'SHSW-1': {'name': "Shelly 1"},
    'SHSW-21': {'name': "Shelly 2"},
    'SHSW-22': {'name': "Shelly HD Pro"},
    'SHSW-25': {'name': "Shelly 2.5"},
    'SHSW-44': {'name': "Shelly 4 Pro"},
    'SHPLG-1': {'name': "Shelly Plug"},
    'SHPLG2-1': {'name': "Shelly Plug"},
    'SHPLG-S': {'name': "Shelly Plug S"},
    'SHRGBWW-01': {'name': "Shelly RGBWW"},
    'SHBLB-1': {'name': "Shelly Bulb"},
    'SHHT-1': {'name': "Shelly H&T"},
    'SHRGBW2': {'name': "Shelly RGBW2"},
    'SHEM': {'name': "Shelly EM"},
    'SHCL-255': {'name': "Shelly Bulb"},
    'SH2LED-1': {'name': "Shelly 2LED"},
    'SHSK-1': {'name': "Shelly Socket"},
    'SHSW-PM': {'name': "Shelly 1 PM"},
    'SHWT-1': {'name': "Shelly Flood"},
    'SHDM-1': {'name': "Shelly Dimmer"},
}

EFFECTS_RGBW2 = [
    {'name': "Off", 'effect': 0},
    {'name': "Meteor shower", 'effect': 1},
    {'name':"Gradual change", 'effect': 2},
    {'name': "Flash", 'effect': 3}
]

EFFECTS_BULB = [
    {'name': "Off", 'effect': 0},
    {'name': "Meteor shower", 'effect': 1},
    {'name': "Gradual change", 'effect': 2},
    {'name':"Breath", 'effect': 3},
    {'name':"Flash", 'effect': 4},
    {'name': "On/off gradual", 'effect': 5},
    {'name':"Red/green change", 'effect': 6},
]

class pyShellyBlock():
    def __init__(self, parent, id, type, ip_addr, code):
        self.id = id
        self.type = type
        self.parent = parent
        self.ip_addr = ip_addr
        self.devices = []
        self.code = code  # DEBUG
        self.cb_updated = []
        self.unavailable_after_sec = None
        self._setup()
        self.info_values = {}
        self._last_update_status_info = None
        self._reload = False
        self.last_updated = datetime.now()
        self.error = None

    def update(self, data, ip):
        self.ip_addr = ip  # If changed ip
        self.last_updated = datetime.now()
        for dev in self.devices:
            dev.ip_addr = ip
            if hasattr(dev, 'update'):
                dev.update(data)
        if self._reload:
            self._reload_devices()
            for device in self.devices:
                if hasattr(device, 'update'):
                    device.update(data)
                self.parent.add_device(device, self.code)
            self._reload = False

    def _raise_updated(self):
        for callback in self.cb_updated:
            callback(self)

    def update_status_information(self):
        """Update the status information."""
        self._last_update_status_info = datetime.now()

        status = self.http_get('/status', False)
        if status == {}:
            return

        #Put status in info_values
        info_values = {}
        for name, attr in BLOCK_INFO_VALUES.items():
            data = status
            path = attr[ATTR_PATH]                        
            for key in path.split('/'):
                data = data.get(key,None) if data is not None else None
            if data is not None:
                fmt = attr.get(ATTR_FMT, None)
                if fmt == "round":
                    data = round(data, 0)
                info_values[name] = data

        if info_values.get(INFO_VALUE_CLOUD_ENABLED):
            if info_values.get(INFO_VALUE_CLOUD_CONNECTED):
                info_values[INFO_VALUE_CLOUD_STATUS] = 'connected'
            else:
                info_values[INFO_VALUE_CLOUD_STATUS] = 'disconnected'
        else:
            info_values[INFO_VALUE_CLOUD_STATUS] = 'disabled'

        self.info_values = info_values
        self._raise_updated()

        for dev in self.devices:
            dev.update_status_information(status)

    def http_get(self, url, log_error=True):
        """Send HTTP GET request"""
        try:
            resp_json = None
            _LOGGER.debug("http://%s%s", self.ip_addr, url)
            conn = httplib.HTTPConnection(self.ip_addr)
            headers = {}
            if self.parent.username is not None \
               and self.parent.password is not None:
                combo = '%s:%s' % (self.parent.username, self.parent.password)
                auth = s(
                    base64.b64encode(combo.encode()))  # .replace('\n', '')
                headers["Authorization"] = "Basic %s" % auth
            conn.request("GET", url, None, headers)
            resp = conn.getresponse()

            if resp.status == 200:
                body = resp.read()
                _LOGGER.debug("Body: %s", body)
                resp_json = json.loads(s(body))
                self.error = ""
            else:
                self.error = "Error, " + str(resp.status) \
                                + ' ' + str(resp.reason)
                _LOGGER.debug(self.error)
            conn.close()
            return resp_json
        except Exception as ex:
            if log_error:
                _LOGGER.exception(
                    "Error http GET: http://%s%s %s %s", self.ip_addr, url,
                    ex, traceback.format_exc())
            else:
                _LOGGER.debug(
                    "Fail http GET: %s", ex)
            return {}

    def update_firmware(self):
        """Start firmware update"""
        self.http_get("/ota?update=1")

    def _setup(self):
        #Shelly BULB
        if self.type == 'SHBLB-1' or self.type == 'SHCL-255':
            self._add_device(pyShellyBulb(self))
        #Shelly 2
        elif self.type == 'SHSW-21':
            settings = self.http_get("/settings")
            if settings.get('mode') == 'roller':
                self._add_device(pyShellyRoller(self))
            else:
                self._add_device(pyShellyRelay(self, 1, 112, 111, 118))
                self._add_device(pyShellyRelay(self, 2, 122, None, 128))
            self._add_device(pyShellySwitch(self, 1, 118))
            self._add_device(pyShellySwitch(self, 2, 128))
            self._add_device(pyShellyPowerMeter(self, 0, [111]))
        #Shelly 2.5
        elif self.type == 'SHSW-25':
            settings = self.http_get("/settings")
            if settings.get('mode') == 'roller':
                self._add_device(pyShellyRoller(self))
                self._add_device(pyShellyPowerMeter(self, 1, [111, 112]))
            else:
                self._add_device(pyShellyRelay(self, 1, 112, 111, 118))
                self._add_device(pyShellyRelay(self, 2, 122, 121, 128))
                self._add_device(pyShellyPowerMeter(self, 1, [111]))
                self._add_device(pyShellyPowerMeter(self, 2, [121]))
            self._add_device(pyShellySwitch(self, 1, 118))
            self._add_device(pyShellySwitch(self, 2, 128))
                #self._add_device(pyShellyInfoSensor(self, 'temperature'))
        elif self.type == 'SHSW-22':
            self._add_device(pyShellyRelay(self, 1, 112, 111))
            self._add_device(pyShellyRelay(self, 2, 122, 121))
            self._add_device(pyShellyPowerMeter(self, 1, [111]))
            self._add_device(pyShellyPowerMeter(self, 2, [121]))
        elif self.type == 'SH2LED-1':
            self._add_device(pyShellyRGBW2W(self, 0))
            self._add_device(pyShellyRGBW2W(self, 1))
        elif self.type == 'SHEM':
            self._add_device(pyShellyRelay(self, 1, 112))
            self._add_device(pyShellyPowerMeter(self, 1, [111]))
            self._add_device(pyShellyPowerMeter(self, 2, [121]))
        #Shelly 1
        elif self.type == 'SHSW-1' or self.type == 'SHSK-1':
            self._add_device(pyShellyRelay(self, 0, 112, None, 118))
            self._add_device(pyShellySwitch(self, 0, 118))
        #Shelly 1 PM
        elif self.type == 'SHSW-PM':
            self._add_device(pyShellyRelay(self, 0, 112, 111, 118))
            self._add_device(pyShellyPowerMeter(self, 0, [111]))
            self._add_device(pyShellySwitch(self, 0, 118))
        #Shelly 4 Pro
        elif self.type == 'SHSW-44':
            for channel in range(4):
                pos = 112 + (channel * 10)
                self._add_device(pyShellyRelay(self, channel + 1, pos, pos-1))
                self._add_device(pyShellyPowerMeter(self, channel + 1,
                                                    [pos - 1]))
        elif self.type == 'SHRGBWW-01':
            self._add_device(pyShellyRGBWW(self))
        #Shelly Dimmer
        elif self.type == 'SHDM-1':
            self._add_device(pyShellyDimmer(self, 121, 111))
            self._add_device(pyShellySwitch(self, 1, 131))
            self._add_device(pyShellySwitch(self, 2, 141))
        #Shelly PLUG'S
        elif (self.type == 'SHPLG-1' or self.type == 'SHPLG2-1' or
              self.type == 'SHPLG-S'):
            self._add_device(pyShellyRelay(self, 0, 112, 111))
            self._add_device(pyShellyPowerMeter(self, 0, [111]))
        elif self.type == 'SHHT-1':
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(pyShellySensor(self, 33, 'temperature'))
            self._add_device(pyShellySensor(self, 44, 'humidity'))
        elif self.type == 'SHRGBW2':
            settings = self.http_get("/settings")
            if settings.get('mode', 'color') == 'color':
                self._add_device(pyShellyRGBW2C(self))
            else:
                for channel in range(4):
                    self._add_device(pyShellyRGBW2W(self, channel + 1))
        elif self.type == 'SHWT-1':
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(pyShellyFlood(self))
            self._add_device(pyShellySensor(self, 33, 'temperature'))
        #else:
        #    self._add_device(pyShellyUnknown(self))

    def _add_device(self, dev):
        self.devices.append(dev)
        #self.parent.add_device(dev, self.code)
        return dev

    def _reload_devices(self):
        for device in self.devices:
            self.parent.remove_device(device, self.code)
            device._close()
        self.devices = []
        self._setup()

    def type_name(self):
        """Type friendly name"""
        try:
            name = SHELLY_TYPES[self.type]['name']
        except:
            name = self.type
        return name

    def available(self):
        """Return if device available"""
        if self.unavailable_after_sec is None:
            return True
        if self.last_updated is None:
            return False
        diff = datetime.now() - self.last_updated
        return diff.total_seconds() <= self.unavailable_after_sec

class pyShellyDevice(object):
    def __init__(self, block):
        self.block = block
        self.id = block.id
        self.type = block.type
        self.ip_addr = block.ip_addr
        self.cb_updated = []        
        self.is_device = True
        self.is_sensor = False
        self.sub_name = None
        self.state_values = None
        self.sensor_values = None
        self.info_values = None
        self.state = None
        self.device_type = None
        self.device_sub_type = None #Used to make sensors unique

    def type_name(self):
        """Friendly type name"""
        try:
            name = SHELLY_TYPES[self.type]['name']
        except:
            name = self.type
        if self.sub_name is not None:
            name = name + " (" + self.sub_name + ")"
        return name

    def _send_command(self, url):
        self.block.http_get(url)

    def available(self):
        return self.block.available()

    def _update(self, new_state=None, new_state_values=None, new_values=None,
                info_values=None):
        _LOGGER.debug("Update id:%s state:%s stateValue:%s values:%s info_values:%s", self.id, new_state,
                     new_state_values, new_values, info_values)        
        need_update = False
        if new_state is not None:
            if self.state != new_state:
                self.state = new_state
                need_update = True
        if new_state_values is not None:
            if self.state_values != new_state_values:
                self.state_values = new_state_values
                need_update = True
        if new_values is not None:
            self.sensor_values = new_values
            need_update = True
        if info_values is not None:
            self.info_values = info_values
            need_update = True
        if need_update:
            self._raise_updated()

    def update_status_information(self,  _status):
        """Update the status information."""
        pass
        #self._update(info_values={}})

    def _raise_updated(self):
        for callback in self.cb_updated:
            callback(self)

    def _close(self):
        self.cb_updated = []

    def _reload_block(self):
        self.block._reload = True

class pyShellyUnknown(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyUnknown, self).__init__(block)
        self.device_type = "UNKNOWN"

    def update(self, data):
        pass

class pyShellyRelay(pyShellyDevice):
    def __init__(self, block, channel, pos, power_idx=None, switch_idx=None):
        super(pyShellyRelay, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += '-' + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._pos = pos
        self._power_idx = power_idx
        self._switch_idx = switch_idx
        self.state = None
        self.device_type = "RELAY"
        self.is_sensor = power_idx is not None

    def update(self, data):
        new_state = data.get(self._pos) == 1
        new_values = {}
        if self._power_idx is not None:
            consumption = data.get(self._power_idx)
            new_values[INFO_VALUE_CONSUMPTION] = consumption
        if self._switch_idx is not None:
            switch_state = data.get(self._switch_idx)
            new_values[INFO_VALUE_SWITCH] = switch_state
        self._update(new_state, None, new_values)

    def update_status_information(self, status):
        """Update the status information."""
        info_values = {}
        relays = status.get(STATUS_RESPONSE_RELAYS)
        if relays:
            relay = relays[self._channel]
            if relay.get(STATUS_RESPONSE_RELAY_OVER_POWER) is not None:
                info_values[INFO_VALUE_OVER_POWER] = \
                    relay.get(STATUS_RESPONSE_RELAY_OVER_POWER)

        self._update(info_values=info_values)

    def turn_on(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=on")

    def turn_off(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=off")


class pyShellyPowerMeter(pyShellyDevice):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, positions):
        super(pyShellyPowerMeter, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._positions = positions
        self.sensor_values = {}
        self.device_type = "POWERMETER"

    def update(self, data):
        """Get the power"""
        consumption = sum(data.get(pos, 0) for pos in self._positions)
        self._update(None, None, {INFO_VALUE_CONSUMPTION: consumption})

class pyShellySwitch(pyShellyDevice):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, position):
        super(pyShellySwitch, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._position = position
        self.sensor_values = {}
        self.device_type = "SWITCH"

    def update(self, data):
        """Get the power"""
        state = data.get(self._position)
        self._update(None, None, {INFO_VALUE_SWITCH: state})

class pyShellyRoller(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyRoller, self).__init__(block)
        self.id = block.id
        self.device_type = "ROLLER"
        self.state = None
        self.position = None
        self.is_sensor = True
        self.sub_name = "Roller"
        self.support_position = False
        self.motion_state = ""
        self.last_direction = ""
        settings = self.block.http_get("/roller/0")
        self.support_position = settings.get("positioning", False)

    def update(self, data):
        #self.motion_state = settings.get("state", False)
        #self.last_direction = settings.get("last_direction")
        self.motion_state = ""
        if data.get(112):
            self.motion_state = "open"
        if data.get(122):
            self.motion_state = "close"
        if self.motion_state:
            self.last_direction = self.motion_state
        self.position = data.get(113)
        consumption = data.get(111, 0) + data.get(121, 0)
        state = self.position != 0
        self._update(state, None, {INFO_VALUE_CONSUMPTION:consumption})

    def up(self):
        self._send_command("/roller/0?go=" + ("open"))

    def down(self):
        self._send_command("/roller/0?go=" + ("close"))

    def stop(self):
        self._send_command("/roller/0?go=stop")

    def set_position(self, pos):
        self._send_command("/roller/0?go=to_pos&roller_pos=" + str(pos))

class pyShellyDimmer(pyShellyDevice):
    def __init__(self, block, state_pos, dim_pos):
        super(pyShellyDimmer, self).__init__(block)
        self.id = block.id
        self.device_type = "DIMMER"
        self.url = "/light/0"
        self.state = None
        self.brightness = None
        self.state_pos = state_pos
        self.dim_pos = dim_pos

    def update(self, data):
        new_state = data.get(self.state_pos) == 1
        self.brightness = data.get(self.dim_pos)        
        values = { 'brightness': self.brightness }        
        self._update(new_state, values)

    def _send_data(self, state, brightness=None):
        url = self.url + "?"

        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                self._send_command(url)
                return
            url += "turn=on&"

        if brightness is not None:
            url += "brightness=" + str(brightness) + "&"

        self._send_command(url)

    def turn_on(self, brightness=None):
        self._send_data(True, brightness)

    #def set_values(self, brightness=None):
    #    self._send_data(None, brightness)

    def turn_off(self):
        self._send_data(False)

    def get_dim_value(self):
        return self.brightness

    def set_dim_value(self, value):
        self._send_data(True, value)

class pyShellyLight(pyShellyDevice):
    def __init__(self, block, state_pos):
        super(pyShellyLight, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "LIGHT"
        self.url = "/light/0"

        self.mode = None
        self.brightness = None
        self.white_value = None
        self.rgb = None
        self.temp = None
        self.effect = None

        self.effects_list = None
        self.allow_switch_mode = True
        self.support_color_temp = False
        self.support_white_value = False

        self.state_pos = state_pos

    def update(self, data):
        settings = self.block.http_get(self.url)
        _LOGGER.debug(settings)
        mode = settings.get('mode', 'color')
        if mode != self.mode:
            if not self.allow_switch_mode and self.mode is not None:
                self._reload_block()
                return
            self.mode = mode

        new_state = data.get(self.state_pos) == 1

        if self.mode == 'color':
            self.brightness = int(settings.get('gain', 0))
            self.white_value = int(settings.get('white', 0))
        else:
            self.brightness = int(settings.get('brightness', 0))

        self.rgb = [data.get(111), data.get(121), data.get(131)]

        self.temp = int(settings.get('temp', 0))

        self.effect = int(settings.get('effect', 0))

        values = {'mode': self.mode, 'brightness': self.brightness,
                  'rgb': self.rgb, 'temp': self.temp,
                  'white_value': self.white_value,
                  'effect': self.effect}

        self._update(new_state, values)

    def _send_data(self, state, brightness=None, rgb=None, temp=None, mode=None,
                   effect=None, white_value=None):
        url = self.url + "?"

        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                self._send_command(url)
                return

            url += "turn=on&"

        if mode is not None:
            self._send_command("/settings/?mode=" + mode)
        else:
            mode = self.mode

        if effect is not None:
            self._send_command("/color/0/?effect=" + str(effect))

        if brightness is not None:
            if mode == "white":
                url += "brightness=" + str(brightness) + "&"
            else:
                url += "gain=" + str(brightness) + "&"

        if white_value is not None:
            url += "white=" + str(white_value) + "&"

        if rgb is not None:
            url += "red=" + str(rgb[0]) + "&"
            url += "green=" + str(rgb[1]) + "&"
            url += "blue=" + str(rgb[2]) + "&"

        if temp is not None:
            url += "temp=" + str(temp) + "&"

        self._send_command(url)

    def turn_on(self, rgb=None, brightness=None, temp=None, mode=None,
                effect=None, white_value=None):
        self._send_data(True, brightness, rgb, temp, mode, effect, white_value)

    def set_values(self, rgb=None, brightness=None, temp=None, mode=None,
                   effect=None, white_value=None):
        self._send_data(None, brightness, rgb, temp, mode, effect, white_value)

    def turn_off(self):
        self._send_data(False)

    def get_dim_value(self):
        return self.brightness

    def set_dim_value(self, value):
        self._send_data(True, value)

    def get_white_value(self):
        return self.white_value

    def set_white_value(self, value):
        self._send_data(True, white_value=value)

class pyShellyBulb(pyShellyLight):
    def __init__(self, block):
        super(pyShellyBulb, self).__init__(block, 181)
        self.effects_list = EFFECTS_BULB
        self.support_color_temp = True

class pyShellyRGBWW(pyShellyLight):
    def __init__(self, block):
        super(pyShellyRGBWW, self).__init__(block, 151)
        self.support_color_temp = True

class pyShellyRGBW2W(pyShellyLight):
    def __init__(self, block, channel):
        super(pyShellyRGBW2W, self).__init__(block, 161)
        self.id = self.id + '-' + str(channel)
        self._channel = channel - 1
        self.mode = "white"
        self.url = "/white/" + str(channel - 1)
        self.effects_list = None
        self.allow_switch_mode = False

    def update(self, data):
        if 181 in data:
            new_state = data.get(151 + self._channel * 10) == 1
            self.brightness = data.get(111 + self._channel * 10)
            values = {'mode': self.mode, 'brightness': self.brightness}
                      #'rgb': self.rgb, 'temp': self.temp}
            self._update(new_state, values)
        else:
            self._reload_block()

class pyShellyRGBW2C(pyShellyLight):
    def __init__(self, block):
        super(pyShellyRGBW2C, self).__init__(block, 161)
        self.mode = "color"
        self.url = "/color/0"
        self.effects_list = EFFECTS_RGBW2
        self.allow_switch_mode = False
        self.support_white_value = True

class pyShellySensor(pyShellyDevice):
    def __init__(self, block, pos, type):        
        super(pyShellySensor, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "SENSOR"
        self.device_sub_type = type
        self.is_sensor = True
        self.is_device = False
        self._pos = pos
        self.sensor_type = type

    def update(self, data):
        value = float(data.get(self._pos))
        self._update(None, None, { self.sensor_type : value })


class pyShellyBinarySensor(pyShellySensor):
    def __init__(self, block, pos, type):        
        super(pyShellyBinarySensor, self).__init__(block, pos, type)

    def update(self, data):
        value = bool(data.get(self._pos))
        self._update(None, None, { self.sensor_type : value })

class pyShellyFlood(pyShellyBinarySensor):
    """Class to represent a power meter value"""
    def __init__(self, block):
        super(pyShellyFlood, self).__init__(block, 23, 'flood')

class pyShelly():
    def __init__(self):
        _LOGGER.info("Init pyShelly %s", VERSION)
        self.stopped = threading.Event()
        self.blocks = {}
        self.devices = []
        self.cb_block_added = []
        self.cb_device_added = []
        self.cb_device_removed = []
        # Used if igmp packages not sent correctly
        self.igmp_fix_enabled = False
        self.username = None
        self.password = None
        self.update_status_interval = None
        self._main_thread = None
        self._socket = None
        self.only_device_id = None

    def open(self):
        self.init_socket()
        self._main_thread = threading.Thread(target=self._main_loop)
        self._main_thread.daemon = True
        self._main_thread.start()

    def version(self):
        return VERSION

    def init_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                          socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
        s.bind(('', COAP_PORT))
        mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP),
                           socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        s.settimeout(15)
        self._socket = s

    def close(self):
        self.stopped.set()
        if self._main_thread is not None:
            self._main_thread.join()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self._socket.close()

    def discover(self):
        msg = bytes(b'\x50\x01\x00\x0A\xb3cit\x01d\xFF')
        self._socket.sendto(msg, (COAP_IP, COAP_PORT))

    #def update_status_information(self):
    #    """Update status information for all blocks."""
    #    for _, block in self.blocks.items():
    #        block.update_status_information()

    def add_device(self, dev, code):
        _LOGGER.debug('Add device')
        self.devices.append(dev)
        for callback in self.cb_device_added:
            callback(dev, code)
    
    def remove_device(self, dev, code):
        _LOGGER.debug('Remove device')
        self.devices.remove(dev)
        for callback in self.cb_device_removed:
            callback(dev, code)

    def _main_loop(self):

        next_igmp_fix = datetime.now() + timedelta(minutes=1)

        while not self.stopped.isSet():

            try:

                # This fix is needed if not sending IGMP reports correct
                if self.igmp_fix_enabled and datetime.now() > next_igmp_fix:
                    _LOGGER.debug("IGMP fix")
                    next_igmp_fix = datetime.now() + timedelta(minutes=1)
                    mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP),
                                       socket.INADDR_ANY)
                    try:
                        self._socket.setsockopt(socket.IPPROTO_IP,
                                                socket.IP_DROP_MEMBERSHIP,
                                                mreq)
                    except Exception as e:
                        _LOGGER.debug("Can't drop membership, " + str(e))
                    try:
                        self._socket.setsockopt(socket.IPPROTO_IP,
                                                socket.IP_ADD_MEMBERSHIP, mreq)
                    except Exception as e:
                        _LOGGER.debug("Can't add membership, " + str(e))

                #_LOGGER.debug("Wait for UDP message")

                try:
                    dataTmp, addr = self._socket.recvfrom(500)
                except socket.timeout:
                    continue

                ipaddr = addr[0]

                #_LOGGER.debug("Got UDP message")

                data = bytearray(dataTmp)
                #_LOGGER.debug(" Data: %s", data)

                pos = 0

                """Receice messages with ip from proxy"""
                if data[0]==112 and data[1]==114 and data[2]==120 and data[3]==121:
                    ipaddr = socket.inet_ntoa(data[4:8])
                    pos = 8

                byte = data[pos]
                #ver = byte >> 6
                #typex = (byte >> 4) & 0x3
                #tokenlen = byte & 0xF

                code = data[pos+1]
                #msgid = 256 * data[2] + data[3]

                pos = pos + 4

                #_LOGGER.debug(' Code: %s', code)

                if code == 30 or code == 69:

                    byte = data[pos]
                    totDelta = 0

                    device_type = ''
                    id = ''

                    while byte != 0xFF:
                        delta = byte >> 4
                        length = byte & 0x0F

                        if delta == 13:
                            pos = pos + 1
                            delta = data[pos] + 13
                        elif delta == 14:
                            pos = pos + 2
                            delta = data[pos - 1] * 256 + data[pos] + 269

                        totDelta = totDelta + delta

                        if length == 13:
                            pos = pos + 1
                            length = data[pos] + 13
                        elif length == 14:
                            pos = pos + 2
                            length = data[pos - 1] * 256 + data[pos] + 269

                        value = data[pos + 1:pos + length]
                        pos = pos + length + 1

                        if totDelta == 3332:
                            device_type, id, _ = s(value).split('#', 2)

                        byte = data[pos]

                    payload = s(data[pos + 1:])

                    if self.only_device_id is not None and \
                            id != self.only_device_id:
                        continue

                    _LOGGER.debug(' Type %s, Id %s, Payload *%s*', device_type, 
                                  id, payload.replace(' ', ''))

                    if code == 30:
                        
                        block_added = False
                        if id not in self.blocks:
                            block = self.blocks[id] = \
                                pyShellyBlock(self, id, device_type, ipaddr, code)
                            block_added = True

                        data = {d[1]:d[2] for d in json.loads(payload)['G']}
                        block = self.blocks[id]
                        if self.update_status_interval is not None and \
                            (block._last_update_status_info is None or
                            datetime.now() - block._last_update_status_info > self.update_status_interval):
                            t = threading.Thread(target=block.update_status_information)
                            t.daemon = True
                            t.start()
                        block.update(data, ipaddr)

                        if block_added:
                            for callback in self.cb_block_added:
                                callback(block)
                            for device in block.devices:
                                self.add_device(device, block.code)

            except Exception as e:

                _LOGGER.exception(
                    "Error receiving UDP: %s, %s", e, traceback.format_exc())
