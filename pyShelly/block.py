"""Block is a physical device"""
# pylint: disable=broad-except, bare-except

from datetime import datetime
from .utils import shelly_http_get
from .switch import Switch
from .relay import Relay
from .powermeter import PowerMeter
from .sensor import Sensor, Flood, DoorWindow, ExtTemp
from .light import RGBW2W, RGBW2C, RGBWW, Bulb, Duo
from .dimmer import Dimmer
from .roller import Roller
from .utils import exception_log

from .const import (
    LOGGER,
    SENSOR_UNAVAILABLE_SEC,
    INFO_VALUE_CLOUD_STATUS,
    INFO_VALUE_CLOUD_ENABLED,
    INFO_VALUE_CLOUD_CONNECTED,
    INFO_VALUE_FW_VERSION,
    INFO_VALUE_PAYLOAD,
    ATTR_PATH,
    ATTR_FMT,
    BLOCK_INFO_VALUES,
    SHELLY_TYPES
)

class Block():
    def __init__(self, parent, block_id, block_type, ip_addr, discovery_src):
        self.id = block_id
        self.unit_id = block_id
        self.type = block_type
        self.parent = parent
        self.ip_addr = ip_addr
        self.devices = []
        self.discovery_src = discovery_src
        self.cb_updated = []
        self.unavailable_after_sec = None
        self.info_values = {}
        self.last_update_status_info = None
        self.reload = False
        self.last_updated = None #datetime.now()
        self.error = None
        self.discover_by_mdns = False
        self.discover_by_coap = False
        self.sleep_device = False
        self.payload = None
        self.settings = None
        self._setup()
        self._available = None

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
                self.parent.add_device(device, self.discovery_src)
            self.reload = False

    def raise_updated(self):
        for callback in self.cb_updated:
            callback(self)

    def update_status_information(self):
        """Update the status information."""
        self.last_update_status_info = datetime.now()

        if self.available() != self._available:
            self._available = self.available()
            self.raise_updated()
            for dev in self.devices:
                dev.raise_updated()

        LOGGER.debug("Get status from %s %s", self.id, self.friendly_name())
        success, status = self.http_get('/status', False)
        #LOGGER.debug(status)
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
                    data = round(data)
                info_values[name] = data

        if self.payload:
            info_values[INFO_VALUE_PAYLOAD] = self.payload

        if info_values.get(INFO_VALUE_CLOUD_ENABLED):
            if info_values.get(INFO_VALUE_CLOUD_CONNECTED):
                info_values[INFO_VALUE_CLOUD_STATUS] = 'connected'
            else:
                info_values[INFO_VALUE_CLOUD_STATUS] = 'disconnected'
        else:
            info_values[INFO_VALUE_CLOUD_STATUS] = 'disabled'

        self.info_values = info_values
        self.raise_updated()

        for dev in self.devices:
            try:
                dev.update_status_information(status)
                dev.raise_updated()
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

    def poll_settings(self):
        if self.type in SHELLY_TYPES and \
            SHELLY_TYPES[self.type].get('battery'):
                return
        success, settings = self.http_get("/settings")
        if success:
            self.settings = settings

    def _setup(self):
        #Get settings
        self.poll_settings()
        #Shelly BULB
        if self.type == 'SHBLB-1' or self.type == 'SHCL-255':
            self._add_device(Bulb(self))
        #Shelly 2
        elif self.type == 'SHSW-21':
            if self.settings:
                if self.settings.get('mode') == 'roller':
                    self._add_device(Roller(self))
                else:
                    self._add_device(Relay(self, 1, 112, 111, 118))
                    self._add_device(Relay(self, 2, 122, None, 128))
                self._add_device(Switch(self, 1, 118))
                self._add_device(Switch(self, 2, 128))
                self._add_device(PowerMeter(self, 0, [111]))
            #else delayed reload
        #Shelly 2.5
        elif self.type == 'SHSW-25':
            if self.settings:
                if self.settings.get('mode') == 'roller':
                    self._add_device(Roller(self))
                    self._add_device(PowerMeter(self, 1, [111, 121], [0,1]))
                else:
                    self._add_device(Relay(self, 1, 112, 111, 118))
                    self._add_device(Relay(self, 2, 122, 121, 128))
                    self._add_device(PowerMeter(self, 1, [111]))
                    self._add_device(PowerMeter(self, 2, [121]))
                self._add_device(Switch(self, 1, 118))
                self._add_device(Switch(self, 2, 128))
                #self._add_device(InfoSensor(self, 'temperature'))
            #todo delayed reload
        elif self.type == 'SHSW-22':
            self._add_device(Relay(self, 1, 112, 111))
            self._add_device(Relay(self, 2, 122, 121))
            self._add_device(PowerMeter(self, 1, [111]))
            self._add_device(PowerMeter(self, 2, [121]))
        elif self.type == 'SH2LED-1':
            self._add_device(RGBW2W(self, 0))
            self._add_device(RGBW2W(self, 1))
        elif self.type == 'SHEM':
            self._add_device(Relay(self, 0, 112))
            self._add_device(PowerMeter(self, 1, [111], voltage_to_block=True))
            self._add_device(PowerMeter(self, 2, [121], voltage_to_block=True))
        #Shelly 3EM
        elif self.type == 'SHEM-3':
            self._add_device(Relay(self, 0, 112))
            self._add_device(PowerMeter(self, 1, [111], None, 116, 114, 115))
            self._add_device(PowerMeter(self, 2, [121], None, 126, 124, 125))
            self._add_device(PowerMeter(self, 3, [131], None, 136, 134, 135))
        #Shelly 1
        elif self.type == 'SHSW-1' or self.type == 'SHSK-1':
            self._add_device(Relay(self, 0, 112, None, 118))
            self._add_device(Switch(self, 0, 118))
            self._add_device(ExtTemp(self, 0), True)
            self._add_device(ExtTemp(self, 1), True)
            self._add_device(ExtTemp(self, 2), True)
        #Shelly 1 PM
        elif self.type == 'SHSW-PM':
            self._add_device(Relay(self, 0, 112, 111, 118))
            self._add_device(PowerMeter(self, 0, [111]))
            self._add_device(Switch(self, 0, 118))
            self._add_device(ExtTemp(self, 0), True)
            self._add_device(ExtTemp(self, 1), True)
            self._add_device(ExtTemp(self, 2), True)
        #Shelly 4 Pro
        elif self.type == 'SHSW-44':
            for channel in range(4):
                relay_pos = 112 + (channel * 10)
                power_pos = 111 + (channel * 10)
                switch_pos = 118 + (channel * 10)
                self._add_device(
                    Relay(self, channel + 1, relay_pos, power_pos, switch_pos))
                self._add_device(PowerMeter(self, channel + 1, [power_pos]))
                self._add_device(Switch(self, channel + 1, switch_pos))
        elif self.type == 'SHRGBWW-01':
            self._add_device(RGBWW(self))
        #Shelly Dimmer
        elif self.type == 'SHDM-1':
            self._add_device(Dimmer(self, 121, 111))
            self._add_device(Switch(self, 1, 131))
            self._add_device(Switch(self, 2, 141))
            self._add_device(PowerMeter(self, 0, None), True)
        #Shelly PLUG'S
        elif (self.type == 'SHPLG-1' or self.type == 'SHPLG2-1' or
              self.type == 'SHPLG-S'):
            self._add_device(Relay(self, 0, 112, 111))
            self._add_device(PowerMeter(self, 0, [111]))
        elif self.type == 'SHHT-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(Sensor(self, 33, 'temperature', 'tmp/value'))
            self._add_device(Sensor(self, 44, 'humidity', 'hum/value'))
        elif self.type == 'SHRGBW2':
            if self.settings:
                if self.settings.get('mode', 'color') == 'color':
                    self._add_device(RGBW2C(self))
                else:
                    for channel in range(4):
                        self._add_device(RGBW2W(self, channel + 1))
            self._add_device(Switch(self, 0, 118))
            #todo else delayed reload
        #Shelly Flood
        elif self.type == 'SHWT-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(Flood(self))
            self._add_device(Sensor(self, 33, 'temperature', 'tmp/value'))
        elif self.type == 'SHDW-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(DoorWindow(self))
            self._add_device(Sensor(self, 66, 'illuminance', 'lux/value'))
        elif self.type == 'SHBDUO-1':
            self._add_device(Duo(self))

    def _add_device(self, dev, lazy_load=False):
        dev.lazy_load = lazy_load
        self.devices.append(dev)
        #self.parent.add_device(dev, self.discovery_src)
        return dev

    def _reload_devices(self):
        for device in self.devices:
            self.parent.remove_device(device, self.discovery_src)
            device.close()
        self.devices = []
        self._setup()

    def fw_version(self):
        return self.info_values.get(INFO_VALUE_FW_VERSION)

    def friendly_name(self):
        try:
            if self.parent.cloud:
                name = self.parent.cloud.get_device_name(self.id.lower())
                if name:
                    return name
        except:
            pass
        return self.type_name() + ' - ' + self.id

    def room_name(self):
        if self.parent.cloud:
            return self.parent.cloud.get_room_name(self.id.lower())

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
