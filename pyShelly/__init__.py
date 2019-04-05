# -*- coding: utf-8 -*-

import base64
from datetime import datetime, timedelta
import json
import logging
import socket
import struct
import sys
import threading
import traceback

logger = logging.getLogger('pyShelly')

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

name = "pyShelly"

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

STATUS_RESPONSE_WIFI_STA_RSSI = 'rssi'
STATUS_RESPONSE_WIFI_STA = 'wifi_sta'
STATUS_RESPONSE_WIFI_STA_SSID = 'ssid'
STATUS_RESPONSE_UPDATE = 'update'
STATUS_RESPONSE_UPDATE_HAS_UPDATE = 'has_update'
STATUS_RESPONSE_UPDATE_NEW_VERSION = 'new_version'
STATUS_RESPONSE_UPDATE_OLD_VERSION = 'old_version'
STATUS_RESPONSE_UPTIME = 'uptime'

__version__ = "0.0.23"
VERSION = __version__

SHELLY_TYPES = {
    'SHSW-1': {'name': "Shelly 1"},
    'SHSW-21': {'name': "Shelly 2"},
    'SHSW-22': {'name': "Shelly HD Pro"},
    'SHSW-25': {'name': "Shelly 2.5"},
    'SHSW-44': {'name': "Shelly 4 Pro"},
    'SHPLG-1': {'name': "Shelly Plug"},
    'SHPLG2-1': {'name': "Shelly Plug"},
    'SHRGBWW-01': {'name': "Shelly RGBWW"},
    'SHBLB-1': {'name': "Shelly Bulb"},
    'SHHT-1': {'name': "Shelly H&T"},
    'SHRGBW2': {'name': "Shelly RGBW2"},
    'SHEM-1': {'name': "Shelly EM"},
    'SHCL-255': {'name': "Shelly Bulb"},
    'SH2LED-1': {'name': "Shelly 2LED"},
    'SHSK-1': {'name': "Shelly Socket"},
}


# SHSEN-1    Sense
# SHSM-01    Smoke

class pyShellyBlock():
    def __init__(self, parent, id, type, ipaddr, code):
        self.id = id
        self.type = type
        self.parent = parent
        self.ipaddr = ipaddr
        self.devices = []
        self.code = code  # DEBUG
        self._setup()

    def update(self, data, ip):
        # logger.debug("BlockUpdate %s", data)
        self.ipaddr = ip  # If changed ip
        for dev in self.devices:
            dev.ipaddr = ip
            dev.update(data)

    def update_status_information(self):
        """Update the status information."""
        status = self._httpGet('/status')
        if status == {}:
            return

        info_values = {}

        wifi_sta = status.get(STATUS_RESPONSE_WIFI_STA)
        if wifi_sta is not None:
            if wifi_sta.get(STATUS_RESPONSE_WIFI_STA_RSSI):
                info_values['rssi'] = \
                    wifi_sta.get(STATUS_RESPONSE_WIFI_STA_RSSI)
            if wifi_sta.get(STATUS_RESPONSE_WIFI_STA_SSID):
                info_values['ssid'] = \
                    wifi_sta.get(STATUS_RESPONSE_WIFI_STA_SSID)

        update = status.get(STATUS_RESPONSE_UPDATE)
        if update is not None:
            has_update = False
            if update.get(STATUS_RESPONSE_UPDATE_HAS_UPDATE) is not None:
                has_update = update.get(STATUS_RESPONSE_UPDATE_HAS_UPDATE)
                info_values['has_update'] = has_update

            if update.get(STATUS_RESPONSE_UPDATE_OLD_VERSION):
                info_values['fw_version'] = \
                    update.get(STATUS_RESPONSE_UPDATE_OLD_VERSION)

            if has_update and update.get(STATUS_RESPONSE_UPDATE_NEW_VERSION):
                info_values['new_fw_version'] = \
                    update.get(STATUS_RESPONSE_UPDATE_NEW_VERSION)

        if status.get(STATUS_RESPONSE_UPTIME) is not None:
            info_values['uptime'] = status.get(STATUS_RESPONSE_UPTIME)

        for dev in self.devices:
            dev.update_status_information(info_values)

    def _httpGet(self, url):
        try:
            conn = httplib.HTTPConnection(self.ipaddr)
            headers = {}
            if self.parent.username is not None and self.parent.password is not None:
                combo = '%s:%s' % (self.parent.username, self.parent.password)
                auth = s(
                    base64.b64encode(combo.encode()))  # .replace('\n', '')
                headers["Authorization"] = "Basic %s" % auth
            conn.request("GET", url, None, headers)
            resp = conn.getresponse()
            body = resp.read()
            conn.close()
            logger.debug("Body: %s", body)
            respJson = json.loads(body)
            return respJson
        except:
            return {}

    def _setup(self):
        if self.type == 'SHBLB-1' or self.type == 'SHCL-255':
            self._addDevice(pyShellyBulb(self))
        elif self.type == 'SHSW-21':
            settings = self._httpGet("/settings")
            if settings.get('mode') == 'roller':
                self._addDevice(pyShellyRoller(self))
            else:
                self._addDevice(pyShellyRelay(self, 1, 0, 2))
                self._addDevice(pyShellyRelay(self, 2, 1, 2))
            self._addDevice(pyShellyPowerMeter(self, 0, 2))
        elif self.type == 'SHSW-25':
            settings = self._httpGet("/settings")
            if settings.get('mode') == 'roller':
                self._addDevice(pyShellyRoller(self))
            else:
                self._addDevice(pyShellyRelay(self, 1, 0, 1))
                self._addDevice(pyShellyRelay(self, 2, 2, 3))
                self._addDevice(pyShellyPowerMeter(self, 1, 1))
                self._addDevice(pyShellyPowerMeter(self, 2, 3))
        elif self.type == 'SHSW-22':
            self._addDevice(pyShellyRelay(self, 1, 0, 1))
            self._addDevice(pyShellyRelay(self, 2, 2, 3))
            self._addDevice(pyShellyPowerMeter(self, 1, 1))
            self._addDevice(pyShellyPowerMeter(self, 2, 3))
        elif self.type == 'SH2LED-1':
            self._addDevice(pyShellyRGBW2W(self, 0))
            self._addDevice(pyShellyRGBW2W(self, 1))
        elif self.type == 'SHEM-1':
            self._addDevice(pyShellyRelay(self, 1, 0, 1))
        elif self.type == 'SHSW-1' or self.type == 'SHSK-1':
            self._addDevice(pyShellyRelay(self, 0, 0))
        elif self.type == 'SHSW-44':
            for ch in range(4):
                self._addDevice(
                    pyShellyRelay(self, ch + 1, ch * 2 + 1, ch * 2))
        elif self.type == 'SHRGBWW-01':
            self._addDevice(pyShellyRGBWW(self))
        elif self.type == 'SHPLG-1' or self.type == 'SHPLG2-1':
            self._addDevice(pyShellyRelay(self, 0, 1, 0))
            self._addDevice(pyShellyPowerMeter(self, 0, 0))
        elif self.type == 'SHHT-1':
            self._addDevice(pyShellySensor(self))
        elif self.type == 'SHRGBW2':
            settings = self._httpGet("/settings")
            if settings.get('mode', 'color') == 'color':
                self._addDevice(pyShellyRGBW2C(self))
            else:
                for ch in range(4):
                    self._addDevice(pyShellyRGBW2W(self, ch + 1))
        else:
            self._addDevice(pyShellyUnknown(self))

    def _addDevice(self, dev):
        self.devices.append(dev)
        self.parent._addDevice(dev, self.code)
        return dev

    def _removeDevice(self, dev):
        self.devices.remove(dev)
        self.parent._removeDevice(dev, self.code)
        if len(self.devices) == 0:
            self._setup()


class pyShellyDevice(object):
    def __init__(self, block):
        self.block = block
        self.id = block.id
        self.type = block.type
        self.ipaddr = block.ipaddr
        self.cb_updated = []
        self.lastUpdated = datetime.now()
        self.isDevice = True
        self.isSensor = False
        self.subName = None
        self._unavailableAfterSec = 20
        self.stateValues = None
        self.infoValues = None

    def typeName(self):
        try:
            name = SHELLY_TYPES[self.type]['name']
        except:
            name = self.type
        if self.subName is not None:
            name = name + " (" + self.subName + ")"
        return name

    def _sendCommand(self, url):
        self.block._httpGet(url)

    def available(self):
        if self.lastUpdated is None:
            return False
        diff = datetime.now() - self.lastUpdated
        return diff.total_seconds() < self._unavailableAfterSec

    def _update(self, newState=None, newStateValues=None, newValues=None,
                infoValues=None):
        logger.debug("Update state:%s stateValue:%s values:%s", newState,
                     newStateValues, newValues)
        self.lastUpdated = datetime.now()
        needUpdate = False
        if newState is not None:
            if self.state != newState:
                self.state = newState
                needUpdate = True
        if newStateValues is not None:
            if self.stateValues != newStateValues:
                self.stateValues = newStateValues
                needUpdate = True
        if newValues is not None:
            self.sensorValues = newValues
            needUpdate = True
        if infoValues is not None:
            self.infoValues = infoValues
            needUpdate = True
        if needUpdate:
            self._raiseUpdated()

    def update_status_information(self, info_values):
        """Update the status information."""
        self._update(infoValues=info_values)

    def _raiseUpdated(self):
        for callback in self.cb_updated:
            callback()

    def _removeMySelf(self):
        self.block._removeDevice(self)


class pyShellyUnknown(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyUnknown, self).__init__(block)
        self.devType = "UNKNOWN"

    def update(self, data):
        pass


class pyShellyRelay(pyShellyDevice):
    def __init__(self, block, channel, pos, power=None):
        super(pyShellyRelay, self).__init__(block)
        self.id = block.id;
        if channel > 0:
            self.id += '-' + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._pos = pos
        self._power = power
        self.state = None
        self.devType = "RELAY"
        self.isSensor = power is not None

    def update(self, data):
        newState = data['G'][self._pos][2] == 1
        newValues = None
        if self._power is not None:
            watt = data['G'][self._power][2]
            newValues = {'watt': watt}
        self._update(newState, None, newValues)

    def turnOn(self):
        self._sendCommand("/relay/" + str(self._channel) + "?turn=on")

    def turnOff(self):
        self._sendCommand("/relay/" + str(self._channel) + "?turn=off")


class pyShellyPowerMeter(pyShellyDevice):
    def __init__(self, block, channel, pos):
        super(pyShellyPowerMeter, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._pos = pos
        self.sensorValues = None
        self.devType = "POWERMETER"

    def update(self, data):
        watt = data['G'][self._pos][2]
        self._update(None, None, {'watt': watt})


class pyShellyRoller(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyRoller, self).__init__(block)
        self.id = block.id
        self.devType = "ROLLER"
        self.state = None
        self.position = None
        self.isSensor = True
        self.subName = "Roller"
        self.supportPosition = False
        self.motionState = None
        self.lastDirection = None

    def update(self, data):
        states = data['G']
        settings = self.block._httpGet("/roller/0")
        self.supportPosition = settings.get("positioning", False)
        self.motionState = settings.get("state", False)
        self.lastDirection = settings.get("last_direction")
        self.position = settings.get('current_pos', 0)
        watt = data['G'][2][2]
        state = self.position != 0
        self._update(state, None, {'watt': watt})

    def up(self):
        self._sendCommand("/roller/0?go=" + ("open"))

    def down(self):
        self._sendCommand("/roller/0?go=" + ("close"))

    def stop(self):
        self._sendCommand("/roller/0?go=stop")

    def position(self, pos):
        self._sendCommand("/roller/0?roller_pos=" + str(pos))


class pyShellyLight(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyLight, self).__init__(block)
        self.id = block.id
        self.state = None
        self.devType = "LIGHT"
        self.url = "/light/0"

        self.mode = None
        self.brightness = None
        self.rgb = None
        self.temp = None

        self.supportEffects = True
        self.allowSwitchMode = True
        self.supportColorTemp = False

    def update(self, data):

        settings = self.block._httpGet(self.url)
        logger.debug(settings)

        newState = data['G'][4][2] == 1  # 151
        mode = settings.get('mode', 'color')

        if mode != self.mode:
            if not self.allowSwitchMode and self.mode is not None:
                self._removeMySelf()
                return
            self.mode = mode

        if self.mode == 'color':
            self.brightness = int(settings.get('gain', 0))
        else:
            self.brightness = int(settings.get('brightness', 0))

        self.rgb = [data['G'][0][2], data['G'][1][2], data['G'][2][2]]

        self.temp = int(settings.get('temp', 0))

        values = {'mode': self.mode, 'brightness': self.brightness,
                  'rgb': self.rgb, 'temp': self.temp}
        self._update(newState, values)

    def _sendData(self, state, brightness=None, rgb=None, temp=None, mode=None,
                  effect=None):
        url = self.url + "?"

        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                self._sendCommand(url)
                return

            url += "turn=on&"

        if mode is not None:
            self._sendCommand("/settings/?mode=" + mode)
        else:
            mode = self.mode

        if effect is not None:
            self._sendCommand("/settings/light/0/?effect=" + str(effect))

        if brightness is not None:
            if mode == "white":
                url += "brightness=" + str(brightness) + "&"
            else:
                url += "gain=" + str(brightness) + "&"

        if rgb is not None:
            url += "red=" + str(rgb[0]) + "&"
            url += "green=" + str(rgb[1]) + "&"
            url += "blue=" + str(rgb[2]) + "&"

        if temp is not None:
            url += "temp=" + str(temp) + "&"

        self._sendCommand(url)

    def turnOn(self, rgb=None, brightness=None, temp=None, mode=None,
               effect=None):
        self._sendData(True, brightness, rgb, temp, mode, effect)

    def setValues(self, rgb=None, brightness=None, temp=None, mode=None,
                  effect=None):
        self._sendData(None, brightness, rgb, temp, mode, effect)

    def turnOff(self):
        self._sendData(False)

    def getDimValue(self):
        return self.brightness

    def setDimValue(self, value):
        self._sendData(True, value)


class pyShellyBulb(pyShellyLight):
    def __init__(self, block):
        super(pyShellyBulb, self).__init__(block)
        self.supportColorTemp = True


class pyShellyRGBWW(pyShellyLight):
    def __init__(self, block):
        super(pyShellyRGBWW, self).__init__(block)
        self.supportColorTemp = True


class pyShellyRGBW2W(pyShellyLight):
    def __init__(self, block, channel):
        super(pyShellyRGBW2W, self).__init__(block)
        self.id = self.id + '-' + str(channel)
        self._channel = channel - 1
        self.mode = "white"
        self.url = "/white/" + str(channel - 1)
        self.supportEffects = False
        self.allowSwitchMode = False

    def update(self, data):
        if len(data['G']) == 8:
            newState = data['G'][4 + self._channel][2] == 1
            self.brightness = data['G'][self._channel][2]
            values = {'mode': self.mode, 'brightness': self.brightness,
                      'rgb': self.rgb, 'temp': self.temp}
            self._update(newState, values)
        else:
            self._removeMySelf()


class pyShellyRGBW2C(pyShellyLight):
    def __init__(self, block):
        super(pyShellyRGBW2C, self).__init__(block)
        self.mode = "color"
        self.url = "/color/0"
        self.supportEffects = False
        self.allowSwitchMode = False


class pyShellySensor(pyShellyDevice):
    def __init__(self, block):
        super(pyShellySensor, self).__init__(block)
        self.id = block.id
        self.state = None
        self.devType = "SENSOR"
        self.isSensor = True
        self.isDevice = False
        self._unavailableAfterSec = 3600 * 6  # TODO, read from settings

    def update(self, data):
        temp = float(data['G'][0][2])
        humidity = float(data['G'][1][2])
        battery = int(data['G'][2][2])
        try:
            settings = self.block._httpGet("/settings")
            _unavailableAfterSec = settings['sleep_mode']['period'] * 3600
        except:
            pass
        if humidity == 0:
            # Workaround, not sending humidity in CoAP, will be fixed in next firmware
            try:
                status = self.block._httpGet("/status")
                humidity = status['hum']['value']
            except:
                pass
        self._update(None, None, {'temperature': temp, 'humidity': humidity,
                                  'battery': battery})


class pyShelly():
    def __init__(self):
        logger.info("Init pyShelly %s", VERSION)
        self.stopped = threading.Event()
        self.blocks = {}
        self.devices = []
        self.cb_deviceAdded = None
        self.cb_deviceRemoved = None
        self.igmpFixEnabled = False  # Used if igmp packages not sent correctly
        self.username = None
        self.password = None
        self._udp_thread = None
        self._socket = None

    def open(self):
        self.initSocket()
        self._udp_thread = threading.Thread(target=self._udp_reader)
        self._udp_thread.daemon = True
        self._udp_thread.start()

    def version(self):
        return VERSION

    def initSocket(self):
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
        if self._udp_thread is not None:
            self._udp_thread.join()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self._socket.close()

    def discover(self):
        msg = bytes(b'\x50\x01\x00\x0A\xb3cit\x01d\xFF')
        self._socket.sendto(msg, (COAP_IP, COAP_PORT))

    def update_status_information(self):
        """Update status information for all devices."""
        for device in self.devices:
            device.update_status_information()

    def _addDevice(self, dev, code):
        logger.debug('Add device')
        self.devices.append(dev)
        if self.cb_deviceAdded is not None:
            self.cb_deviceAdded(dev, code)

    def _removeDevice(self, dev, code):
        logger.debug('Remove device')
        self.devices.remove(dev)
        if self.cb_deviceRemoved is not None:
            self.cb_deviceRemoved(dev, code)

    def _udp_reader(self):

        nextIGMPfix = datetime.now() + timedelta(minutes=1)

        while not self.stopped.isSet():

            try:

                # This fix is needed if not sending IGMP reports correct
                if self.igmpFixEnabled and datetime.now() > nextIGMPfix:
                    logger.debug("IGMP fix")
                    nextIGMPfix = datetime.now() + timedelta(minutes=1)
                    mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP),
                                       socket.INADDR_ANY)
                    try:
                        self._socket.setsockopt(socket.IPPROTO_IP,
                                                socket.IP_DROP_MEMBERSHIP,
                                                mreq)
                    except Exception as e:
                        logger.debug("Can't drop membership, " + str(e))
                    try:
                        self._socket.setsockopt(socket.IPPROTO_IP,
                                                socket.IP_ADD_MEMBERSHIP, mreq)
                    except Exception as e:
                        logger.debug("Can't add membership, " + str(e))

                logger.debug("Wait for UDP message")

                try:
                    dataTmp, addr = self._socket.recvfrom(500)
                except socket.timeout:
                    continue

                logger.debug("Got UDP message")

                data = bytearray(dataTmp)
                logger.debug(" Data: %s", data)

                byte = data[0]
                ver = byte >> 6
                typex = (byte >> 4) & 0x3
                tokenlen = byte & 0xF

                code = data[1]
                msgid = 256 * data[2] + data[3]

                pos = 4

                logger.debug(' Code: %s', code)

                if code == 30 or code == 69:

                    byte = data[pos]
                    totDelta = 0

                    devType = "";
                    id = "";

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
                        pos = pos + length + 1;

                        if totDelta == 3332:
                            devType, id, _ = s(value).split('#', 2)

                        byte = data[pos]

                    payload = s(data[pos + 1:])

                    logger.debug(' Type %s, Id %s, Payload *%s*', devType, id,
                                 payload.replace(' ', ''))

                    if id not in self.blocks:
                        self.blocks[id] = pyShellyBlock(self, id, devType,
                                                        addr[0], code)

                    if code == 30:
                        self.blocks[id].update(json.loads(payload), addr[0])

            except Exception as e:

                logger.exception(
                    "Error receiving UDP: " + str(e) + traceback.format_exc())
