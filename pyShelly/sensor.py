# -*- coding: utf-8 -*-

from .device import Device

class Sensor(Device):
    def __init__(self, block, pos, device_type, status_attr, index=None):
        super(Sensor, self).__init__(block)
        self.id = block.id
        if index is not None:
            self.id = self.id + "-" + str(index + 1)
        self.state = None
        self.device_type = "SENSOR"
        self.device_sub_type = device_type
        self.is_sensor = True
        self.is_device = False
        self._pos = pos
        self.sensor_type = device_type
        self._status_attr = status_attr

    def update(self, data):
        value = data.get(self._pos)
        if not value is None:
            self._update(None, None, {self.sensor_type:float(value)})

    def update_status_information(self, status):
        """Update the status information."""
        data = status
        for key in self._status_attr.split('/'):
            data = data.get(key, None) if data is not None else None
        if data:
            self._update(None, None, {self.sensor_type:data})

class BinarySensor(Sensor):
    """Abstract class to represent binary sensor"""
    def __init__(self, block, pos, device_type, status_attr):
        super(BinarySensor, self).__init__(block, pos, device_type, status_attr)

    def update(self, data):
        value = bool(data.get(self._pos))
        self._update(None, None, {self.sensor_type : value})

class ExtTemp(Sensor):
    """Class to represent a external temp sensor"""
    def __init__(self, block, idx):
        super(ExtTemp, self).__init__(block, 119+idx*10, 'temperature', \
            'ext_temperature/' + str(idx) + "/tC", idx)
        self.sleep_device = False

class Flood(BinarySensor):
    """Class to represent a flood sensor"""
    def __init__(self, block):
        super(Flood, self).__init__(block, 23, 'flood', 'flood/value')
        self.sleep_device = True

class DoorWindow(BinarySensor):
    """Class to represent a door/window sensor"""
    def __init__(self, block):
        super(DoorWindow, self).__init__(
            block, 55, 'door_window', 'sensor/state')
        self.sleep_device = True