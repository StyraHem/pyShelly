# -*- coding: utf-8 -*-

from .device import Device

class Sensor(Device):
    def __init__(self, block, pos, device_type, info_type):
        super(Sensor, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "SENSOR"
        self.device_sub_type = device_type
        self.is_sensor = True
        self.is_device = False
        self._pos = pos
        self.sensor_type = device_type
        self.info_type = info_type

    def update(self, data):
        value = float(data.get(self._pos))
        self._update(None, None, {self.sensor_type : value})

    def update_status_information(self, status):
        """Update the status information."""
        item = status.get(self.info_type)
        if item:
            value = item['value']
            self._update(None, None, {self.sensor_type : value})

class BinarySensor(Sensor):
    def __init__(self, block, pos, device_type):
        super(BinarySensor, self).__init__(block, pos, device_type)

    def update(self, data):
        value = bool(data.get(self._pos))
        self._update(None, None, { self.sensor_type : value })

class Flood(BinarySensor):
    """Class to represent a flood sensor"""
    def __init__(self, block):
        super(Flood, self).__init__(block, 23, 'flood')