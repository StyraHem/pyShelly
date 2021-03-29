# -*- coding: utf-8 -*-
import json
from .device import Device
from .const import (
    INFO_VALUE_HUMIDITY,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_POS,
    ATTR_TOPIC,
    SRC_MQTT
)

class Sensor(Device):
    def __init__(self, block, pos, device_type, path, index=None, topic=None):
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
            ATTR_FMT: self.format,
        }
        if topic:
           self._state_cfg[ATTR_TOPIC] =  topic

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

class BinarySensor(Sensor):
    """Abstract class to represent binary sensor"""
    def __init__(self, block, pos, device_type, status_attr, topic=None):
        super(BinarySensor, self).__init__(block, pos, device_type, status_attr, topic=topic)
        self.device_type = "BINARY_SENSOR"

    def format(self, value):
        if value in ('open','mild','heavy','true') :
            return True
        if value in ('close','none','false'):
            return False
        return bool(value)

class Motion(BinarySensor):
    #{"motion":true,"timestamp":1614416952,"active":true,"vibration":true,"lux":303,"bat":87}
    #{"G":[[0,6107,1],[0,3119,1614417090],[0,3120,1],[0,6110,0],[0,3106,285],[0,3111,87],[0,9103,11]]}
    """Class to represent a external temp sensor"""
    def __init__(self, block):
        super(Motion, self).__init__(block, 6107, \
            'motion', 'sensor/motion', topic="@motion")

class ExtSwitch(Sensor):
    """Class to represent a external temp sensor"""
    def __init__(self, block):
        super(ExtSwitch, self).__init__(block, 3117, \
            'external_switch', 'ext_switch/0/input', topic="/status")
        
class TempSensor(Sensor):
    """Class to represent a external temp sensor"""
    def __init__(self, block):
        super(TempSensor, self).__init__(block, [33, 3101], \
            'temperature', 'tmp/tC', topic="sensor/temperature")
        self._info_value_cfg = { 
            INFO_VALUE_HUMIDITY : { #Used in tellstick
                ATTR_POS: [44, 3103],
                ATTR_PATH: 'hum/value',
                ATTR_FMT: "float",
                ATTR_TOPIC: "sensor/humidity"
            }
        }

class ExtTemp(Sensor):
    """Class to represent a external temp sensor"""
    def __init__(self, block, idx):
        super(ExtTemp, self).__init__(block, [119, 3101], \
            'temperature', 'ext_temperature/' + str(idx) + "/tC", idx, "ext_temperature/$")
        self._info_value_cfg = { 
            INFO_VALUE_HUMIDITY : { #Used in tellstick
                ATTR_POS: [120, 3103],
                ATTR_PATH: 'ext_humidity/' + str(idx) + "/hum",
                ATTR_FMT: "float",
                ATTR_TOPIC: "ext_humidity/$"
            }
        }
        self.sleep_device = False
        self.ext_sensor = idx

class ExtHumidity(Sensor):
    """Class to represent a external humidity sensor"""
    def __init__(self, block, idx):
        super(ExtHumidity, self).__init__(block, [120, 3103], \
            'humidity', 'ext_humidity/' + str(idx) + "/hum", idx, "ext_humidity/$")
        self.sleep_device = False
        self.ext_sensor = 1

class Flood(BinarySensor):
    """Class to represent a flood sensor"""
    def __init__(self, block):
        super(Flood, self).__init__(block, [23, 6106], 'flood', 'flood', topic='sensor/flood')
        self.sleep_device = True

class DoorWindow(BinarySensor):
    """Class to represent a door/window sensor"""
    def __init__(self, block, position):
        super(DoorWindow, self).__init__(
            block, position, 'door_window', 'sensor/state', topic='sensor/state')
        self.sleep_device = True

class Gas(BinarySensor):
    """Class to represent a Gas sensor"""
    def __init__(self, block, position):
        super(Gas, self).__init__(
            block, position, 'gas', 'gas_sensor/alarm_state')

