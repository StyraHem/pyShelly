# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except

from .const import LOGGER, SHELLY_TYPES
from .base import Base

class Device(Base):
    def __init__(self, block):
        super(Device, self).__init__()
        self.block = block
        self.id = block.id
        self.unit_id = block.id
        self.type = block.type
        self.is_device = True
        self.is_sensor = False
        self.sub_name = None
        self.state_values = None
        #self.sensor_values = None
        self.state = None
        self.device_type = None
        self.device_sub_type = None #Used to make sensors unique        
        self.device_nr = None
        self.master_unit = False
        self.head_unit = False
        self.ext_sensor = None

    @property
    def ip_addr(self):
        return self.block.ip_addr

    def cloud_name(self):
        name = None
        try:
            if self.block.parent.cloud:
                device_id = self.id.lower().split('-')
                #add_nr = False
                idx = int(device_id[1]) if len(device_id) > 1 else 0
                name = self.block.parent.cloud.get_device_name(device_id[0],
                                                               idx,
                                                               self.ext_sensor)
        except Exception as ex:
            LOGGER.debug("Error look up name, %s", ex)
        return name

    def device_name(self):
        return self.type_name() + ' - ' + self.id

    def friendly_name(self):
        name = self.cloud_name()
        if not name:
            name = self.device_name()
        return name

    def room_name(self):
        if self.block.parent.cloud:
            device_id = self.id.lower().split('-')
            room = None
            if len(device_id) > 1 and int(device_id[1]) > 1:
                room = self.block.parent.cloud.get_room_name(
                    device_id[0] + "_" + device_id[1])
            if room is None:
                room = self.block.parent.cloud.get_room_name(device_id[0])
            return room

    def type_name(self):
        """Friendly type name"""
        try:
            name = SHELLY_TYPES[self.type]['name']
        except:
            name = self.type
        if self.sub_name is not None:
            name = name + " (" + self.sub_name + ")"
        return name

    def _send_command(self, url=None, topic=None, payload=None, rpc_method=None, rpc_params=None):
        res = False
        if rpc_method and self.block.websocket:
            res = self.block.websocket.send(rpc_method, rpc_params)
        if not res and topic and self.block.mqtt_available:
            res = self.block.parent.send_mqtt(self.block, topic, payload, rpc_method, rpc_params)
        if not res and self.ip_addr and url:
            res, _ = self.block.http_get(url)
        self.block.update_status_interval = None #Force update

    def available(self):
        return self.block.available()

    @property
    def protocols(self):
        return self.block.protocols

    def _update(self, src, new_state=None, new_state_values=None):
        LOGGER.debug("Update id:%s state:%s stateValue:%s", self.id, new_state, new_state_values)
        self._set_state(new_state, src)
        if new_state_values is not None:    #Used to check if need update
            if self.state_values != new_state_values:
                self.state_values = new_state_values
                self.need_update = True
        if self.lazy_load:
            self.block.parent.callback_add_device(self)
        self.raise_updated()

    def update_status_information(self, _status, src):
        """Update the status information."""

    def fw_version(self):
        return self.block.fw_version()

    def close(self):
        self.cb_updated = []

    def _reload_block(self):
        self.block.reload = True

    def loop(self):
        pass

