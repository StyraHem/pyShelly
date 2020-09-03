# -*- coding: utf-8 -*-
"""123"""

from .device import Device

from .utils import notNone

from .const import (
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
    STATUS_RESPONSE_INPUTS_INPUT,
    ATTR_POS,
    ATTR_FMT,
    ATTR_PATH,
    ATTR_CHANNEL
)

class Relay(Device):
    def __init__(self, block, channel, consumption_channel = None,
                 include_power=True, em=False):
        #Todo: common_consumption
        super(Relay, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += '-' + str(channel)
            self._channel = ch = channel - 1
            self.device_nr = channel
        else:
            self._channel = ch = 0
        self.state = None
        self.device_type = "RELAY"
        self._state_cfg = {
            ATTR_POS: [112, 1101],
            ATTR_PATH: 'relays/$/ison',
            ATTR_FMT: 'bool'
        }
        self._info_value_cfg = {
            #Todo add total used and returned 4106, 4107
            INFO_VALUE_SWITCH : {
                ATTR_POS: [118, 2101],
                ATTR_PATH: 'inputs/$/input',
                ATTR_FMT: 'bool'
            },
            INFO_VALUE_OVER_POWER : {
                ATTR_POS: [6102],
                ATTR_PATH: 'relays/$/overpower',
                ATTR_FMT: 'bool'
            }
        }
        if include_power:
            meters = "emeters" if em else "meters"
            divider = None if em else '/60'
            self._info_value_cfg.update({
                INFO_VALUE_CURRENT_CONSUMPTION : {
                    ATTR_POS: [111, 4101, 4102, 4105],
                    ATTR_CHANNEL: notNone(consumption_channel, self._channel),
                    ATTR_PATH: meters + '/$/power',
                    ATTR_FMT: ['float']
                },
                INFO_VALUE_TOTAL_CONSUMPTION : {
                    ATTR_POS: [4103, 4104, 4106],
                    ATTR_CHANNEL: notNone(consumption_channel, self._channel),
                    ATTR_PATH: meters + '/$/total',
                    ATTR_FMT: ['float', divider,'round:2']
                }
            })
        # else:
        #     _info_value_cfg.update({
        #         INFO_VALUE_CURRENT_CONSUMPTION : {
        #             ATTR_POS: [111, 4105],
        #             ATTR_CHANNEL: self._channel,
        #             ATTR_PATH: 'meters/$/power',
        #             ATTR_FMT: ['float']
        #         },
        #         INFO_VALUE_TOTAL_CONSUMPTION : {
        #             ATTR_POS: [4106],
        #             ATTR_CHANNEL: notNone(consumption_channel, self._channel),
        #             ATTR_PATH: 'emeters/$/total',
        #             ATTR_FMT: ['float']
        #         }
        #     )

    def as_light(self):
        if self.block.parent.cloud:
            usage = self.block.parent.cloud.get_relay_usage(self.unit_id,
                                                           self._channel)
            return usage == 'light'

    # def update_coap(self, payload):
    #     new_state = self.coap_get(payload, self._pos) == 1
    #     #if self._power_idx is not None:
    #     #    consumption = data.get(self._power_idx)
    #     #    self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = round(consumption)
    #     #if self._switch_idx is not None:
    #     #    switch_state = data.get(self._switch_idx)
    #     #    self.info_values[INFO_VALUE_SWITCH] = switch_state > 0
    #     self._update(new_state, None, None, self.info_values)

    # def update_status_information(self, status):
    #     """Update the status information."""
    #     new_state = None
    #     relays = status.get(STATUS_RESPONSE_RELAYS)
    #     if relays:
    #         relay = relays[self._channel]
    #         # if relay.get(STATUS_RESPONSE_RELAY_OVER_POWER) is not None:
    #         #     self.info_values[INFO_VALUE_OVER_POWER] = \
    #         #         relay.get(STATUS_RESPONSE_RELAY_OVER_POWER)
    #         if relay.get(STATUS_RESPONSE_RELAY_STATE) is not None:
    #             new_state = relay.get(STATUS_RESPONSE_RELAY_STATE)
    #     # if self._power_idx:
    #     #     meters = status.get(STATUS_RESPONSE_METERS)
    #     #     if meters and len(meters) > 0:
    #     #         idx = min(self._channel, len(meters)-1)
    #     #         meter = meters[idx]
    #     #         if meter.get(STATUS_RESPONSE_METERS_POWER) is not None:
    #     #             self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = \
    #     #                 round(float(meter.get(STATUS_RESPONSE_METERS_POWER)))
    #     #         if meter.get(STATUS_RESPONSE_METERS_TOTAL) is not None:
    #     #             self.info_values[INFO_VALUE_TOTAL_CONSUMPTION] = \
    #     #             round(float(meter.get(STATUS_RESPONSE_METERS_TOTAL)) / 60)

    #     # inputs = status.get(STATUS_RESPONSE_INPUTS)
    #     # if inputs:
    #     #     value = inputs[self._channel]
    #     #     if value.get(STATUS_RESPONSE_INPUTS_INPUT) is not None:
    #     #         self.info_values[INFO_VALUE_SWITCH] = \
    #     #             value.get(STATUS_RESPONSE_INPUTS_INPUT) > 0
    #     self._update(new_state, info_values=self.info_values)

    def turn_on(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=on")

    def turn_off(self):
        self._send_command("/relay/" + str(self._channel) + "?turn=off")
