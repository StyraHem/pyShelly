# -*- coding: utf-8 -*-

from .device import Device

from .const import (
    LOGGER,
    INFO_VALUE_CURRENT_CONSUMPTION,
    STATUS_RESPONSE_ROLLERS,
    STATUS_RESPONSE_ROLLERS_STATE,
    STATUS_RESPONSE_ROLLERS_LAST_DIR,
    STATUS_RESPONSE_ROLLERS_POSITION,
    STATUS_RESPONSE_ROLLERS_POWER,
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
        success, settings = self.block.http_get("/roller/0") #Todo move
        if success:
            self.support_position = settings.get("positioning", False)

    def update_coap(self, payload):
        """Update current state"""
        self.motion_state = ""
        if self.coap_get(payload, [112, 1101]):
            self.motion_state = "open"
        if self.coap_get(payload, [122, 1201]):
            self.motion_state = "close"
        if self.motion_state:
            self.last_direction = self.motion_state
        self.position = self.coap_get(payload, [113])
        self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = \
            self.coap_get(payload, 111, 0) + self.coap_get(payload, 121, 0) + \
                self.coap_get(payload, 4104, 0)
        state = self.position != 0
        self._update(state, None, None, self.info_values)

    def update_status_information(self, status):
        """Update the status information."""
        rollers = status.get(STATUS_RESPONSE_ROLLERS)
        if rollers:
            roller = rollers[0]
            self.support_position = roller.get("positioning", False)
            self.motion_state = roller[STATUS_RESPONSE_ROLLERS_STATE]
            self.last_direction = roller[STATUS_RESPONSE_ROLLERS_LAST_DIR]
            self.position = roller[STATUS_RESPONSE_ROLLERS_POSITION]
            if self.position < 0 or self.position > 100:
                self.position = 0
                self.support_position = False
                LOGGER.warning("Roller \"%s\" is missing calibration, positioning disabled", self.friendly_name())
            self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = \
                roller[STATUS_RESPONSE_ROLLERS_POWER]
            state = self.position != 0
            self._update(state, None, None, self.info_values)

    def up(self):
        self._send_command("/roller/0?go=" + ("open"))

    def down(self):
        self._send_command("/roller/0?go=" + ("close"))

    def stop(self):
        self._send_command("/roller/0?go=stop")

    def set_position(self, pos):
        if self.support_position:
            self._send_command("/roller/0?go=to_pos&roller_pos=" + str(pos))
