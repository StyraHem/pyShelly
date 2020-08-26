# -*- coding: utf-8 -*-

from .device import Device
from .const import (
    INFO_VALUE_VIBRATION,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_POS
)

class Sensor(Device):
    def __init__(self, block, pos, device_type, path, index=None):
        super(Sensor, self).__init__(block)
        self.id = block.id
        self._channel = index or 0
        if index is not None:
            self.id = self.id + "-" + str(index + 1)
            self.device_nr = index + 1
        self.state = None
        self.device_type = "SENSOR"
        self.device_sub_type = device_type
        self.is_sensor = True
        self.is_device = False
        #self._pos = pos
        self.sensor_type = device_type
        #elf._status_attr = path
        self._state_cfg = {
            ATTR_POS: pos,
            ATTR_PATH: path,
            ATTR_FMT: self.format
        }

    def format(self, value):
        return float(value)

    # def update_coap(self, payload):
    #     if self._pos:
    #         value = self.coap_get(payload, self._pos)
    #         if value is not None:
    #             self._update(self.format(value))

    # def update_status_information(self, status):
    #     """Update the status information."""
    #     data = status
    #     for key in self._status_attr.split('/'):
    #         data = data.get(key) if data is not None else None
    #     if data is not None:
    #         #self._update(None, None, {self.sensor_type:self.format(data)})
    #         self._update(self.format(data))

class ExtTemp(Sensor):
    """Class to represent a external temp sensor"""
    def __init__(self, block, idx):
        super(ExtTemp, self).__init__(block, [119, 3101], \
            'temperature', 'ext_temperature/' + str(idx) + "/tC", idx)
        self.sleep_device = False
        self.ext_sensor = idx

class ExtHumidity(Sensor):
    """Class to represent a external humidity sensor"""
    def __init__(self, block, idx):
        super(ExtHumidity, self).__init__(block, [120, 3103], \
            'humidity', 'ext_humidity/' + str(idx) + "/hum", idx)
        self.sleep_device = False
        self.ext_sensor = 1

class BinarySensor(Sensor):
    """Abstract class to represent binary sensor"""
    def __init__(self, block, pos, device_type, status_attr):
        super(BinarySensor, self).__init__(block, pos, device_type, status_attr)
        self.device_type = "BINARY_SENSOR"

    def format(self, value):
        if value == 'open' or value == 'mild' or value == 'heavy' :
            return True
        if value == 'close' or value == 'none':
            return False
        return bool(value)

class Flood(BinarySensor):
    """Class to represent a flood sensor"""
    def __init__(self, block):
        super(Flood, self).__init__(block, 23, 'flood', 'flood')
        self.sleep_device = True

class DoorWindow(BinarySensor):
    """Class to represent a door/window sensor"""
    def __init__(self, block, position):
        super(DoorWindow, self).__init__(
            block, position, 'door_window', 'sensor/state')
        self.sleep_device = True

class Gas(BinarySensor):
    """Class to represent a Gas sensor"""
    def __init__(self, block, position):
        super(Gas, self).__init__(
            block, position, 'gas', 'gas_sensor/alarm_state')

