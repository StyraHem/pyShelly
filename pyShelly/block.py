"""Block is a physical device"""
# pylint: disable=broad-except, bare-except

from datetime import datetime
from .utils import shelly_http_get
from .switch import Switch
from .relay import Relay
from .powermeter import PowerMeter
from .sensor import Sensor, Flood
from .light import RGBW2W, RGBW2C, RGBWW, Dimmer, Bulb
from .roller import Roller
from .utils import exception_log

from .const import (
    LOGGER,
    SENSOR_UNAVAILABLE_SEC,
    INFO_VALUE_CLOUD_STATUS,
    INFO_VALUE_CLOUD_ENABLED,
    INFO_VALUE_CLOUD_CONNECTED,
    ATTR_PATH,
    ATTR_FMT,
    BLOCK_INFO_VALUES,
    SHELLY_TYPES
)

class Block():
    def __init__(self, parent, block_id, block_type, ip_addr, code):
        LOGGER.info("################################################")
        LOGGER.info(block_id)
        self.id = block_id
        self.type = block_type
        self.parent = parent
        self.ip_addr = ip_addr
        self.devices = []
        self.code = code  # DEBUG
        self.cb_updated = []
        self.unavailable_after_sec = None
        self._setup()
        self.info_values = {}
        self.last_update_status_info = None
        self.reload = False
        self.last_updated = None #datetime.now()
        self.error = None

    def update(self, data, ip_addr):
        self.ip_addr = ip_addr  # If changed ip
        self.last_updated = datetime.now()
        for dev in self.devices:
            dev.ip_addr = ip_addr
            if hasattr(dev, 'update'):
                dev.update(data)
        if self.reload:
            self._reload_devices()
            for device in self.devices:
                if hasattr(device, 'update'):
                    device.update(data)
                self.parent.add_device(device, self.code)
            self.reload = False

    def _raise_updated(self):
        for callback in self.cb_updated:
            callback(self)

    def update_status_information(self):
        """Update the status information."""
        self.last_update_status_info = datetime.now()

        LOGGER.info("Get status from %s", self.id)
        success, status = self.http_get('/status', False)
        LOGGER.debug(status)
        if not success or status == {}:
            return

        self.last_updated = datetime.now()

        #Put status in info_values
        info_values = {}
        for name, attr in BLOCK_INFO_VALUES.items():
            data = status
            path = attr[ATTR_PATH]
            for key in path.split('/'):
                data = data.get(key, None) if data is not None else None
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
            try:
                dev.update_status_information(status)
            except Exception as ex:
                exception_log(ex, "Error update device status: {} {}", \
                    dev.id, dev.type)

    def http_get(self, url, log_error=True):
        """Send HTTP GET request"""
        success, res = shelly_http_get(self.ip_addr, url, \
                              self.parent.username, self.parent.password, \
                              log_error)

        return success, res

    def update_firmware(self):
        """Start firmware update"""
        self.http_get("/ota?update=1")

    def _setup(self):
        #Shelly BULB
        if self.type == 'SHBLB-1' or self.type == 'SHCL-255':
            self._add_device(Bulb(self))
        #Shelly 2
        elif self.type == 'SHSW-21':
            success, settings = self.http_get("/settings") #todo
            if settings.get('mode') == 'roller':
                self._add_device(Roller(self))
            else:
                self._add_device(Relay(self, 1, 112, 111, 118))
                self._add_device(Relay(self, 2, 122, None, 128))
            self._add_device(Switch(self, 1, 118))
            self._add_device(Switch(self, 2, 128))
            self._add_device(PowerMeter(self, 0, [111]))
        #Shelly 2.5
        elif self.type == 'SHSW-25':
            _, settings = self.http_get("/settings") #todo
            if settings.get('mode') == 'roller':
                self._add_device(Roller(self))
                self._add_device(PowerMeter(self, 1, [111, 112]))
            else:
                self._add_device(Relay(self, 1, 112, 111, 118))
                self._add_device(Relay(self, 2, 122, 121, 128))
                self._add_device(PowerMeter(self, 1, [111]))
                self._add_device(PowerMeter(self, 2, [121]))
            self._add_device(Switch(self, 1, 118))
            self._add_device(Switch(self, 2, 128))
                #self._add_device(InfoSensor(self, 'temperature'))
        elif self.type == 'SHSW-22':
            self._add_device(Relay(self, 1, 112, 111))
            self._add_device(Relay(self, 2, 122, 121))
            self._add_device(PowerMeter(self, 1, [111]))
            self._add_device(PowerMeter(self, 2, [121]))
        elif self.type == 'SH2LED-1':
            self._add_device(RGBW2W(self, 0))
            self._add_device(RGBW2W(self, 1))
        elif self.type == 'SHEM':
            self._add_device(Relay(self, 1, 112))
            self._add_device(PowerMeter(self, 1, [111]))
            self._add_device(PowerMeter(self, 2, [121]))
        #Shelly 1
        elif self.type == 'SHSW-1' or self.type == 'SHSK-1':
            self._add_device(Relay(self, 0, 112, None, 118))
            self._add_device(Switch(self, 0, 118))
        #Shelly 1 PM
        elif self.type == 'SHSW-PM':
            self._add_device(Relay(self, 0, 112, 111, 118))
            self._add_device(PowerMeter(self, 0, [111]))
            self._add_device(Switch(self, 0, 118))
        #Shelly 4 Pro
        elif self.type == 'SHSW-44':
            for channel in range(4):
                pos = 112 + (channel * 10)
                self._add_device(Relay(self, channel + 1, pos, pos-1))
                self._add_device(PowerMeter(self, channel + 1,
                                                    [pos - 1]))
        elif self.type == 'SHRGBWW-01':
            self._add_device(RGBWW(self))
        #Shelly Dimmer
        elif self.type == 'SHDM-1':
            self._add_device(Dimmer(self, 121, 111))
            self._add_device(Switch(self, 1, 131))
            self._add_device(Switch(self, 2, 141))
        #Shelly PLUG'S
        elif (self.type == 'SHPLG-1' or self.type == 'SHPLG2-1' or
              self.type == 'SHPLG-S'):
            self._add_device(Relay(self, 0, 112, 111))
            self._add_device(PowerMeter(self, 0, [111]))
        elif self.type == 'SHHT-1':
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(Sensor(self, 33, 'temperature', 'tmp'))
            self._add_device(Sensor(self, 44, 'humidity', 'hum'))
        elif self.type == 'SHRGBW2':
            _, settings = self.http_get("/settings") #todo
            if settings.get('mode', 'color') == 'color':
                self._add_device(RGBW2C(self))
            else:
                for channel in range(4):
                    self._add_device(RGBW2W(self, channel + 1))
        elif self.type == 'SHWT-1':
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(Flood(self))
            self._add_device(Sensor(self, 33, 'temperature', 'tmp'))
        #else:
        #    self._add_device(Unknown(self))

    def _add_device(self, dev):
        self.devices.append(dev)
        #self.parent.add_device(dev, self.code)
        return dev

    def _reload_devices(self):
        for device in self.devices:
            self.parent.remove_device(device, self.code)
            device.close()
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
