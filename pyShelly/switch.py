# -*- coding: utf-8 -*-

from .device import Device
from .const import (
    STATUS_RESPONSE_INPUTS,
    STATUS_RESPONSE_INPUTS_INPUT
)

class Switch(Device):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, position):
        super(Switch, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
            self.device_nr = channel
        else:
            self._channel = 0
        self._position = position
        self.sensor_values = {}
        self.device_type = "SWITCH"

    def update(self, data):
        """Get the power"""
        state = data.get(self._position)
        self._update(state > 0)

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        inputs = status.get(STATUS_RESPONSE_INPUTS)
        if inputs:
            value = inputs[self._channel]
            new_state = value.get(STATUS_RESPONSE_INPUTS_INPUT, None)
            self._update(new_state > 0)
