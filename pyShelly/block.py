"""Block is a physical device"""
# pylint: disable=broad-except, bare-except

from datetime import datetime
from .utils import shelly_http_get
from .switch import Switch
from .relay import Relay
from .powermeter import PowerMeter
from .sensor import (Sensor, BinarySensor, Flood, DoorWindow, ExtTemp,
                     ExtHumidity, Gas)
from .light import RGBW2W, RGBW2C, RGBWW, Bulb, Duo, Vintage
from .dimmer import Dimmer
from .roller import Roller
from .utils import exception_log
from .base import Base

from .const import (
    LOGGER,
    SENSOR_UNAVAILABLE_SEC,
    INFO_VALUE_DEVICE_TEMP,
    INFO_VALUE_CLOUD_STATUS,
    INFO_VALUE_CLOUD_ENABLED,
    INFO_VALUE_CLOUD_CONNECTED,
    INFO_VALUE_HAS_FIRMWARE_UPDATE,
    INFO_VALUE_FW_VERSION,
    INFO_VALUE_LATEST_FIRMWARE_VERSION,
    INFO_VALUE_LATEST_BETA_FW_VERSION,
    INFO_VALUE_PAYLOAD,
    INFO_VALUE_BATTERY,
    INFO_VALUE_ILLUMINANCE,
    INFO_VALUE_TILT,
    INFO_VALUE_VIBRATION,
    INFO_VALUE_TEMP,
    INFO_VALUE_GAS,
    INFO_VALUE_SENSOR,
    INFO_VALUE_TOTAL_WORK_TIME,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_POS,
    ATTR_AUTO_SET,
    BLOCK_INFO_VALUES,
    SHELLY_TYPES,
    SRC_STATUS
)

class Block(Base):
    def __init__(self, parent, block_id, block_type, ip_addr, discovery_src):
        super(Block, self).__init__()
        self.id = block_id
        self.unit_id = block_id
        self.type = block_type
        self.parent = parent
        self.ip_addr = ip_addr
        self.devices = []
        self.discovery_src = discovery_src
        self.protocols = []
        self.unavailable_after_sec = None
        #self.info_values = {}
        #self.info_values_updated = {}
        self.last_update_status_info = None
        self.reload = False
        self.last_updated = None #datetime.now()
        self.error = None
        self.discover_by_mdns = False
        self.discover_by_coap = False
        self.sleep_device = False
        self.payload = None
        self.settings = None
        self.exclude_info_values = []
        #self._info_value_cfg = None
        self._setup()
        self._available = None
        self.status_update_error_cnt = 0
        self.last_try_update_status = None

    def update_coap(self, payload, ip_addr):
        self.ip_addr = ip_addr  # If changed ip
        self.last_updated = datetime.now()
        self._update_info_values_coap(payload, BLOCK_INFO_VALUES)   

        if self.payload:
            self.set_info_value(INFO_VALUE_PAYLOAD, self.payload, None)
     
        for dev in self.devices:
            dev.ip_addr = ip_addr
            dev._update_info_values_coap(payload)
            if hasattr(dev, 'update_coap'):
                dev.update_coap(payload)
            dev.raise_updated()
        if self.reload:
            self._reload_devices()
            for dev in self.devices:
                dev._update_info_values_coap(payload)
                if hasattr(dev, 'update_coap'):
                    dev.update_coap(payload)
                self.parent.add_device(dev, self.discovery_src)
            self.reload = False
        self.raise_updated()

    def loop(self):
        if self._info_value_cfg:
            for iv, cfg in self._info_value_cfg.items():
                if ATTR_AUTO_SET in cfg:
                    value = self.info_values.get(iv)
                    param = cfg.get(ATTR_AUTO_SET)
                    new_value = param[0]
                    if value != new_value:
                        time = self.info_values_updated.get(iv)
                        delay = param[1]
                        if time:
                            diff = datetime.now() - time
                            if diff.total_seconds() > delay:
                                self.set_info_value(iv, new_value, None)
                                self.raise_updated()

    def check_available(self):
        if self.available() != self._available:
            self._available = self.available()
            self.raise_updated(True)
            for dev in self.devices:
                dev.raise_updated(True)

    def update_status_information(self):
        """Update the status information."""
        self.last_update_status_info = datetime.now()

        if self.status_update_error_cnt >= 3:
            diff = (datetime.now()-self.last_try_update_status).total_seconds()
            if diff < 600 or (diff < 3600 and self.status_update_error_cnt >= 5):
                return

        self.last_try_update_status = datetime.now()

        LOGGER.debug("Get status from %s %s", self.id, self.friendly_name())
        success, status = self.http_get('/status', False)

        if not success or status == {}:
            self.status_update_error_cnt += 1
            return

        if 'poll' not in self.protocols:
            self.protocols.append("poll")

        self.status_update_error_cnt = 0
        self.last_updated = datetime.now()

        #Put status in info_values
        for name, cfg in BLOCK_INFO_VALUES.items():
            if name in self.exclude_info_values:
                continue
            self._update_info_value(name, status, cfg)

        if self._info_value_cfg:
            for name, cfg in self._info_value_cfg.items():
                self._update_info_value(name, status, cfg)

        cloud_status = 'disabled'
        if self.info_values.get(INFO_VALUE_CLOUD_ENABLED):
            if self.info_values.get(INFO_VALUE_CLOUD_CONNECTED):
                cloud_status = 'connected'
            else:
                cloud_status = 'disconnected'
        self.set_info_value(INFO_VALUE_CLOUD_STATUS, cloud_status, SRC_STATUS)

        #self.info_values[INFO_VALUE_HAS_FIRMWARE_UPDATE] = self.has_fw_update()
        self.set_info_value(INFO_VALUE_LATEST_BETA_FW_VERSION,
                            self.latest_fw_version(True), SRC_STATUS)

        self.raise_updated()

        for dev in self.devices:
            try:
                if dev._state_cfg:
                    dev._update_state(status, dev._state_cfg)
                if dev._info_value_cfg:
                    for name, cfg in dev._info_value_cfg.items():
                        dev._update_info_value(name, status, cfg)
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

    def update_firmware(self, beta = False):
        """Start firmware update"""
        url = None
        if beta:
            url = self.parent._firmware_mgr.url(self.type, False)
        if url:
            self.http_get("/ota?url=" + url)
        else:
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
        #Shelly 1
        elif self.type == 'SHSW-1' or self.type == 'SHSK-1':
            self._add_device(Relay(self, 0))
            self._add_device(Switch(self, 0))
            self._add_device(ExtTemp(self, 0), True)
            self._add_device(ExtTemp(self, 1), True)
            self._add_device(ExtTemp(self, 2), True)
            self._add_device(ExtHumidity(self, 0), True)
        #Shelly 1 PM
        elif self.type == 'SHSW-PM':
            self._add_device(Relay(self, 0))
            self._add_device(PowerMeter(self, 0))
            self._add_device(Switch(self, 0))
            self._add_device(ExtTemp(self, 0), True)
            self._add_device(ExtTemp(self, 1), True)
            self._add_device(ExtTemp(self, 2), True)
            self._add_device(ExtHumidity(self, 0), True)
        #Shelly 2
        elif self.type == 'SHSW-21':
            if self.settings:
                if self.settings.get('mode') == 'roller':
                    self._add_device(Roller(self))
                else:
                    self._add_device(Relay(self, 1))
                    self._add_device(Relay(self, 2, consumption_channel = 0))
                self._add_device(Switch(self, 1))
                self._add_device(Switch(self, 2))
                self._add_device(PowerMeter(self, 0))
        #Shelly 2.5
        elif self.type == 'SHSW-25':
            if self.settings:
                if self.settings.get('mode') == 'roller':
                    self._add_device(Roller(self))
                    self._add_device(PowerMeter(self, 1))
                else:
                    self._add_device(Relay(self, 1))
                    self._add_device(Relay(self, 2))
                    self._add_device(PowerMeter(self, 1))
                    self._add_device(PowerMeter(self, 2))
                    self._add_device(Switch(self, 1))
                    self._add_device(Switch(self, 2))
                #self._add_device(InfoSensor(self, 'temperature'))
            #todo delayed reload
        #Shelly PLUG'S
        elif self.type == 'SHPLG-1' or self.type == 'SHPLG2-1' or \
              self.type == 'SHPLG-S':
            self._add_device(Relay(self, 0))
            self._add_device(PowerMeter(self, 0))
        elif self.type == 'SHEM':
            self._add_device(Relay(self, 0, include_power=False, em=True))
            self._add_device(PowerMeter(self, 1, voltage_to_block=True,
                                        em=True))
            self._add_device(PowerMeter(self, 2, voltage_to_block=True,
                                        em=True))
        #Shelly 3EM
        elif self.type == 'SHEM-3':
            self._add_device(Relay(self, 0, include_power=False, em=True))
            self._add_device(PowerMeter(self, 1, em=True))
            self._add_device(PowerMeter(self, 2, em=True))
            self._add_device(PowerMeter(self, 3, em=True))
        elif self.type == 'SH2LED-1':
            self._add_device(RGBW2W(self, 1))
            self._add_device(RGBW2W(self, 2))
        #Shelly 4 Pro
        elif self.type == 'SHSW-44':
            for channel in range(4):
                self._add_device(Relay(self, channel + 1))
                self._add_device(PowerMeter(self, channel + 1))
                self._add_device(Switch(self, channel + 1))
        elif self.type == 'SHRGBWW-01':
            self._add_device(RGBWW(self))
        #Shelly Dimmer
        elif self.type in ('SHDM-1', 'SHDM-2'):
            #self._info_value_cfg = {INFO_VALUE_DEVICE_TEMP : {ATTR_POS : 311}}
            self._add_device(Dimmer(self, [121, 1101], [111, 5101]))
            self._add_device(Switch(self, 1, position=[131, 2101]))
            self._add_device(Switch(self, 2, position=[131, 2101]))
            self._add_device(PowerMeter(self, 0, 4101, 4103))
        elif self.type == 'SHHT-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self.exclude_info_values.append(INFO_VALUE_DEVICE_TEMP)
            self._add_device(Sensor(self, [33, 3101], 'temperature', 'tmp/tC'))
            self._add_device(Sensor(self, [44, 3103], 'humidity', 'hum/value'))
        #Shellyy RGBW2
        elif self.type == 'SHRGBW2':
            if self.settings:
                if self.settings.get('mode', 'color') == 'color':
                    self._add_device(RGBW2C(self))
                    self._add_device(PowerMeter(self, 0, position=[211, 4101]))
                else:
                    for channel in range(4):
                        self._add_device(RGBW2W(self, channel + 1))
                        self._add_device(PowerMeter(self, channel+1, [211, 4101]))
            self._add_device(Switch(self, 0))
            #todo else delayed reload
        #Shelly Flood
        elif self.type == 'SHWT-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(Flood(self))
            self._add_device(Sensor(self, 33, 'temperature', 'tmp/tC'))
        elif self.type == 'SHDW-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._info_value_cfg = {INFO_VALUE_BATTERY : {ATTR_POS : [77, 3111]},
                                    INFO_VALUE_TILT : {ATTR_POS : [88, 3109]},
                                    INFO_VALUE_VIBRATION : {ATTR_POS : [99, 6110],
                                                    ATTR_AUTO_SET: [0, 60]},
                                    INFO_VALUE_ILLUMINANCE: {ATTR_POS : [66, 3106]}
            }
            self._add_device(DoorWindow(self, [55, 3108]))
        elif self.type == 'SHDW-2':
            self.sleep_device = True
            self.exclude_info_values.append(INFO_VALUE_DEVICE_TEMP)
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._info_value_cfg = {#INFO_VALUE_BATTERY : {ATTR_POS : 3111},
                                    INFO_VALUE_TILT : {ATTR_POS : 3109, ATTR_PATH : 'accel/tilt'},
                                    INFO_VALUE_VIBRATION :
                                        {ATTR_POS : 6110,
                                         ATTR_PATH : 'accel/vibration',
                                         ATTR_AUTO_SET: [0, 60]},
                                    INFO_VALUE_TEMP: {ATTR_POS : 3101}, #Todo
                                    INFO_VALUE_ILLUMINANCE: {ATTR_POS : 3106, ATTR_PATH : 'lux/value'}
            }
            self._add_device(DoorWindow(self, 3108))
        elif self.type == 'SHBDUO-1':
            self._add_device(Duo(self))
            self._add_device(PowerMeter(self, 0, position=[141, 4101],
                                        tot_pos=[214, 4103]))
        elif self.type == 'SHVIN-1':
            self._add_device(Vintage(self))
            self._add_device(PowerMeter(self, 0, position=[141, 4101],
                                        tot_pos=[214, 4103]))
        elif self.type == 'SHBTN-1':
            self.sleep_device = True
            self.unavailable_after_sec = SENSOR_UNAVAILABLE_SEC
            self._add_device(Switch(self, 0, simulate_state=True,
                                    master_unit=True))
        elif self.type == 'SHIX3-1':
            self._add_device(Switch(self, 1, master_unit=True))
            self._add_device(Switch(self, 2))
            self._add_device(Switch(self, 3))
        elif self.type == 'SHGS-1':
            self._info_value_cfg = {INFO_VALUE_GAS : {ATTR_POS : 122},
                                    INFO_VALUE_SENSOR : {ATTR_POS : [118, 2101]}
            }
            self._add_device(Gas(self, 119))
        elif self.type == 'SHAIR-1':
            self._info_value_cfg = {
                INFO_VALUE_TEMP: {ATTR_POS : 119,
                                  ATTR_PATH : 'ext_temperature/0/tC'},
                INFO_VALUE_TOTAL_WORK_TIME: {ATTR_POS : 121,
                                             ATTR_PATH : 'total_work_time'}
            }
            self._add_device(Relay(self, 0))
            self._add_device(PowerMeter(self, 0))
            self._add_device(Switch(self, 0))

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

    def latest_fw_version(self, beta = False):
        if beta:
            return  self.parent._firmware_mgr.version(self.type, True)
        else:
            return self.info_values.get(INFO_VALUE_LATEST_FIRMWARE_VERSION)

    def has_fw_update(self, beta = False):
        latest = self.latest_fw_version(beta)
        current = self.fw_version()
        return latest and current and latest != current

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
