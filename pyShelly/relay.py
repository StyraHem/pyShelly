# -*- coding: utf-8 -*-
"""123"""

from .device import Device

from .const import (
    #LOGGER,
    STATUS_RESPONSE_RELAYS,
    INFO_VALUE_CONSUMPTION,
    STATUS_RESPONSE_RELAY_OVER_POWER,
    INFO_VALUE_OVER_POWER,
    STATUS_RESPONSE_RELAY_STATE,
    INFO_VALUE_SWITCH
)

class Relay(Device):
    def __init__(self, block, channel, pos, power_idx=None, switch_idx=None):
        super(Relay, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += '-' + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._pos = pos
        self._power_idx = power_idx
        self._switch_idx = switch_idx
        self.state = None
        self.device_type = "RELAY"
        self.is_sensor = power_idx is not None

    def update(self, data):
        new_state = data.get(self._pos) == 1
        new_values = {}
        if self._power_idx is not None:
            consumption = data.get(self._power_idx)
            new_values[INFO_VALUE_CONSUMPTION] = consumption
        if self._switch_idx is not None:
            switch_state = data.get(self._switch_idx)
            new_values[INFO_VALUE_SWITCH] = switch_state
        self._update(new_state, None, new_values)

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        info_values = {}
        relays = status.get(STATUS_RESPONSE_RELAYS)
        if relays:
            relay = relays[self._channel]
            if relay.get(STATUS_RESPONSE_RELAY_OVER_POWER) is not None:
                info_values[INFO_VALUE_OVER_POWER] = \
                    relay.get(STATUS_RESPONSE_RELAY_OVER_POWER)
            if relay.get(STATUS_RESPONSE_RELAY_STATE) is not None:
                new_state = relay.get(STATUS_RESPONSE_RELAY_STATE)

            self._update(new_state, info_values=info_values)

    def turn_on(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=on")

    def turn_off(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=off")
