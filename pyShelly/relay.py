# -*- coding: utf-8 -*-
"""123"""

from .device import Device

from .const import (
    #LOGGER,
    INFO_VALUE_CURRENT_CONSUMPTION,
    INFO_VALUE_TOTAL_CONSUMPTION,
    INFO_VALUE_OVER_POWER,
    INFO_VALUE_SWITCH,
    STATUS_RESPONSE_RELAYS,
    STATUS_RESPONSE_RELAY_OVER_POWER,
    STATUS_RESPONSE_RELAY_STATE,
    STATUS_RESPONSE_METERS,
    STATUS_RESPONSE_METERS_POWER,
    STATUS_RESPONSE_METERS_TOTAL,
    STATUS_RESPONSE_INPUTS,
    STATUS_RESPONSE_INPUTS_INPUT
)

class Relay(Device):
    def __init__(self, block, channel, pos, power_idx=None, switch_idx=None):
        super(Relay, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += '-' + str(channel)
            self._channel = channel - 1
            self.device_nr = channel
        else:
            self._channel = 0
        self._pos = pos
        self._power_idx = power_idx
        self._switch_idx = switch_idx
        self.state = None
        self.device_type = "RELAY"
        self.is_sensor = power_idx is not None
        self.info_values = {}

    def update(self, data):
        new_state = data.get(self._pos) == 1
        if self._power_idx is not None:
            consumption = data.get(self._power_idx)
            self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = round(consumption)
        if self._switch_idx is not None:
            switch_state = data.get(self._switch_idx)
            self.info_values[INFO_VALUE_SWITCH] = switch_state > 0
        self._update(new_state, None, None, self.info_values)

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        relays = status.get(STATUS_RESPONSE_RELAYS)
        if relays:
            relay = relays[self._channel]
            if relay.get(STATUS_RESPONSE_RELAY_OVER_POWER) is not None:
                self.info_values[INFO_VALUE_OVER_POWER] = \
                    relay.get(STATUS_RESPONSE_RELAY_OVER_POWER)
            if relay.get(STATUS_RESPONSE_RELAY_STATE) is not None:
                new_state = relay.get(STATUS_RESPONSE_RELAY_STATE)
        meters = status.get(STATUS_RESPONSE_METERS)
        if meters and len(meters) > self._channel:
            meter = meters[self._channel]
            if meter.get(STATUS_RESPONSE_METERS_POWER) is not None:
                self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = \
                    round(float(meter.get(STATUS_RESPONSE_METERS_POWER)))
            if meter.get(STATUS_RESPONSE_METERS_TOTAL) is not None:
                self.info_values[INFO_VALUE_TOTAL_CONSUMPTION] = \
                  round(float(meter.get(STATUS_RESPONSE_METERS_TOTAL)) / 60)

        inputs = status.get(STATUS_RESPONSE_INPUTS)
        if inputs:
            value = inputs[self._channel]
            if value.get(STATUS_RESPONSE_INPUTS_INPUT) is not None:
                self.info_values[INFO_VALUE_SWITCH] = \
                    value.get(STATUS_RESPONSE_INPUTS_INPUT) > 0
        self._update(new_state, info_values=self.info_values)

    def turn_on(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=on")

    def turn_off(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=off")
