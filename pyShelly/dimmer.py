# -*- coding: utf-8 -*-

from .device import Device

from .const import (
    LOGGER,
    STATUS_RESPONSE_LIGHTS,
    STATUS_RESPONSE_LIGHTS_STATE,
    STATUS_RESPONSE_LIGHTS_BRIGHTNESS,
    STATUS_RESPONSE_INPUTS,
    STATUS_RESPONSE_INPUTS_INPUT,
    INFO_VALUE_SWITCH,
    STATUS_RESPONSE_METERS,
    STATUS_RESPONSE_METERS_POWER,
    INFO_VALUE_CURRENT_CONSUMPTION
)

class Dimmer(Device):
    def __init__(self, block, state_pos, dim_pos):
        super(Dimmer, self).__init__(block)
        self.id = block.id
        self.device_type = "DIMMER"
        self.url = "/light/0"
        self.state = None
        self.brightness = None
        self.state_pos = state_pos
        self.dim_pos = dim_pos
        self.info_values = {}

    def update(self, data):
        new_state = data.get(self.state_pos) == 1
        self.brightness = data.get(self.dim_pos)
        values = {'brightness': self.brightness}
        for idx in range(0, 2):
            value = data.get(131 + idx*10)
            if value is not None:
                self.info_values[INFO_VALUE_SWITCH + "_" + str(idx+1)] = value > 0
        #todo, read consumption when firmware fixed
        self._update(new_state, values, None, self.info_values)

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        lights = status.get(STATUS_RESPONSE_LIGHTS)
        values = {}
        if lights:
            light = lights[0]
            new_state = light.get(STATUS_RESPONSE_LIGHTS_STATE, None)
            self.brightness = \
                light.get(STATUS_RESPONSE_LIGHTS_BRIGHTNESS, None)
            values['brightness'] = self.brightness
        inputs = status.get(STATUS_RESPONSE_INPUTS)
        if inputs:
            for idx in range(0, 2):
                value = inputs[idx]
                if value.get(STATUS_RESPONSE_INPUTS_INPUT) is not None:
                    self.info_values[INFO_VALUE_SWITCH + "_" + str(idx+1)] = \
                        value.get(STATUS_RESPONSE_INPUTS_INPUT) > 0
        meters = status.get(STATUS_RESPONSE_METERS)
        if meters and len(meters) > 0:
            meter = meters[0]
            if meter.get(STATUS_RESPONSE_METERS_POWER) is not None:
                self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] = \
                    round(float(meter.get(STATUS_RESPONSE_METERS_POWER)))
        self._update(new_state, values, None, self.info_values)

    def _send_data(self, state, brightness=None):
        url = self.url + "?"
        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                self._send_command(url)
                return
            url += "turn=on&"
        if brightness is not None:
            url += "brightness=" + str(brightness) + "&"

        self._send_command(url)

    def turn_on(self, brightness=None):
        self._send_data(True, brightness)

    def turn_off(self):
        self._send_data(False)

    def get_dim_value(self):
        return self.brightness

    def set_dim_value(self, value):
        self._send_data(True, value)
