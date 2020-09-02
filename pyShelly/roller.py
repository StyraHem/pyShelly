# -*- coding: utf-8 -*-

from .device import Device

from .const import (
    LOGGER,
    INFO_VALUE_CURRENT_CONSUMPTION,
    INFO_VALUE_TOTAL_CONSUMPTION,
    STATUS_RESPONSE_ROLLERS,
    STATUS_RESPONSE_ROLLERS_STATE,
    STATUS_RESPONSE_ROLLERS_LAST_DIR,
    STATUS_RESPONSE_ROLLERS_POSITION,
    STATUS_RESPONSE_ROLLERS_POWER,
    STATUS_RESPONSE_ROLLERS_TOTAL,
    ATTR_POS,
    ATTR_FMT,
    ATTR_PATH,
    SRC_COAP, SRC_STATUS
)

class Roller(Device):
    def __init__(self, block):
        super(Roller, self).__init__(block)
        self.id = block.id
        self.device_type = "ROLLER"
        self.state = None
        self.position = None
        self.is_sensor = True
        self.sub_name = "Roller"
        self.support_position = False
        self.motion_state = ""
        self.last_direction = ""
        self.info_values = {}
        #success, settings = self.block.http_get("/roller/0") #Todo move
        #if success:
        #    self.support_position = settings.get("positioning", False)
        self._info_value_cfg = {
            INFO_VALUE_TOTAL_CONSUMPTION : {
                ATTR_POS: [4104],
                ATTR_PATH: 'meters/$/total',
                ATTR_FMT: ['float','/60','round:2']
            }
        }

    def _set_pos(self, pos):
        if pos is None or pos < 0 or pos > 100:
            self.position = None
            self.support_position = False
        else:
            self.position = pos
            self.support_position = True

    def update_coap(self, payload):
        """Update current state"""
        self.motion_state = self.coap_get(payload, [1102]) or "stop"
        if self.coap_get(payload, [112]):
            self.motion_state = "open"
        if self.coap_get(payload, [122]):
            self.motion_state = "close"
        if self.motion_state and self.motion_state!="stop":
            self.last_direction = self.motion_state
        self._set_pos(self.coap_get(payload, [113, 1103]))
        self.set_info_value(INFO_VALUE_CURRENT_CONSUMPTION,
            self.coap_get(payload, 111, 0) + self.coap_get(payload, 121, 0) + \
                self.coap_get(payload, 4102, 0), SRC_COAP)
        state = self.position != 0
        self._update(SRC_COAP, state)

    def update_status_information(self, status):
        """Update the status information."""
        rollers = status.get(STATUS_RESPONSE_ROLLERS)
        if rollers:
            roller = rollers[0]
            self.support_position = roller.get("positioning", False)
            self.motion_state = roller[STATUS_RESPONSE_ROLLERS_STATE]
            self.last_direction = roller[STATUS_RESPONSE_ROLLERS_LAST_DIR]
            self._set_pos(roller[STATUS_RESPONSE_ROLLERS_POSITION])
            self.set_info_value(INFO_VALUE_CURRENT_CONSUMPTION,
                                roller[STATUS_RESPONSE_ROLLERS_POWER],
                                SRC_STATUS)
            state = self.position != 0
            self._update(SRC_STATUS, state)

    def up(self):
        self._send_command("/roller/0?go=open")

    def down(self):
        self._send_command("/roller/0?go=close")

    def stop(self):
        self._send_command("/roller/0?go=stop")

    def set_position(self, pos):
        if self.support_position:
            self.position=pos
            self.raise_updated(True)
            self._send_command("/roller/0?go=to_pos&roller_pos=" + str(pos))
