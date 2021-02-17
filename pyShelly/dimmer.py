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
    INFO_VALUE_CURRENT_CONSUMPTION,
    SRC_COAP, SRC_STATUS
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
        self.is_sensor = True

    def update_coap(self, payload):
        new_state = self.coap_get(payload, self.state_pos) == 1
        self.brightness = self.coap_get(payload, self.dim_pos)
        values = {'brightness': self.brightness}
        for idx in range(0, 2):
            value = self.coap_get(payload, [131, 2101], channel=idx)
            if value is not None:
                self.set_info_value(INFO_VALUE_SWITCH + "_" + str(idx+1),
                                    value > 0, SRC_COAP)
        consumption = self.coap_get(payload, [4101])
        if consumption is not None:
            self.set_info_value(INFO_VALUE_CURRENT_CONSUMPTION,
                                    float(consumption), SRC_COAP)

            #if value is not None:
            #    self.info_values[INFO_VALUE_SWITCH + "_" + str(idx+1)] = value > 0
        #todo, read consumption when firmware fixed
        self._update(SRC_COAP,new_state, values)

    def update_status_information(self, status, src):
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
                input = inputs[idx]
                value = input.get(STATUS_RESPONSE_INPUTS_INPUT)
                if value is not None:
                    self.set_info_value(INFO_VALUE_SWITCH + "_" + str(idx+1),
                                         value > 0, src)
        meters = status.get(STATUS_RESPONSE_METERS)
        if meters and len(meters) > 0:
            meter = meters[0]
            value = meter.get(STATUS_RESPONSE_METERS_POWER)
            if value is not None:
                self.set_info_value(INFO_VALUE_CURRENT_CONSUMPTION,
                                     float(value), src)

        self._update(src, new_state, values)

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
