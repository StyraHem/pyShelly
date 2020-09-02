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
        self.ip_addr = block.ip_addr
        self.is_device = True
        self.is_sensor = False
        self.sub_name = None
        self.state_values = None
        #self.sensor_values = None
        self.state = None
        self.device_type = None
        self.device_sub_type = None #Used to make sensors unique
        self.lazy_load = False
        self.device_nr = None
        self.master_unit = False
        self.ext_sensor = None

    def friendly_name(self):
        try:
            if self.block.parent.cloud:
                device_id = self.id.lower().split('-')
                name = None
                #add_nr = False
                idx = int(device_id[1]) if len(device_id) > 1 else 0
                name = self.block.parent.cloud.get_device_name(device_id[0],
                                                               idx,
                                                               self.ext_sensor)

                # if len(device_id) > 1 and int(device_id[1]) > 1:
                #     cloud_id = device_id[0] + '_' + str(int(device_id[1])-1)
                #     name = self.block.parent.cloud.get_device_name(cloud_id,
                #                                                self.ext_sensor)
                #     if not name:
                #         add_nr = True
                # if not name:
                #     name = \
                #       self.block.parent.cloud.get_device_name(device_id[0],
                #                                               self.ext_sensor)
                #     if add_nr:
                #         name += " - " + device_id[1]
                if name:
                    return name
        except Exception as ex:
            LOGGER.debug("Error look up name, %s", ex)
        name = self.type_name() + ' - ' + self.id
        #if self.device_nr:
        #   name += ' - ' + str(self.device_nr)
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

    def _send_command(self, url):
        self.block.http_get(url)
        self.block.update_status_interval = None #Force update

    def available(self):
        return self.block.available()

    @property
    def protocols(self):
        return self.block.protocols

    def _update(self, src, new_state=None, new_state_values=None):
        LOGGER.debug(
            "Update id:%s state:%s stateValue:%s",
            self.id, new_state, new_state_values)
        self._set_state(new_state, src)
        if new_state_values is not None:
            if self.state_values != new_state_values:
                self.state_values = new_state_values
                self.need_update = True
        #if new_values is not None:
        #    self.sensor_values = new_values
        #    self.need_update = True
        #if info_values is not None:
        #    self.info_values = info_values
        #    self.need_update = True
        if self.lazy_load:
            self.block.parent.callback_add_device(self)
        self.raise_updated()

    def update_status_information(self, _status):
        """Update the status information."""

    def fw_version(self):
        return self.block.fw_version()

    def close(self):
        self.cb_updated = []

    def _reload_block(self):
        self.block.reload = True

    def loop(self):
        pass

