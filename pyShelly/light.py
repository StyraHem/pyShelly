# -*- coding: utf-8 -*-

from .device import Device

from .const import (
    LOGGER,
    EFFECTS_BULB,
    EFFECTS_RGBW2,
    STATUS_RESPONSE_LIGHTS,
    STATUS_RESPONSE_LIGHTS_STATE,
    STATUS_RESPONSE_LIGHTS_BRIGHTNESS,
    STATUS_RESPONSE_LIGHTS_RED,
    STATUS_RESPONSE_LIGHTS_GREEN,
    STATUS_RESPONSE_LIGHTS_BLUE,
    STATUS_RESPONSE_LIGHTS_MODE
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

    def update(self, data):
        new_state = data.get(self.state_pos) == 1
        self.brightness = data.get(self.dim_pos)
        values = { 'brightness': self.brightness}
        self._update(new_state, values)

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
            self._update(new_state, values)

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

    #def set_values(self, brightness=None):
    #    self._send_data(None, brightness)

    def turn_off(self):
        self._send_data(False)

    def get_dim_value(self):
        return self.brightness

    def set_dim_value(self, value):
        self._send_data(True, value)

class Light(Device):
    def __init__(self, block, state_pos, channel=0):
        super(Light, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "LIGHT"
        self.url = "/light/0"

        self.mode = None
        self.brightness = None
        self.white_value = None
        self.rgb = None
        self.temp = None
        self.effect = None

        self.effects_list = None
        self.allow_switch_mode = True
        self.support_color_temp = False
        self.support_white_value = False

        self.state_pos = state_pos
        self._channel = channel

    def update(self, data):
        settings = self.block.http_get(self.url) #todo
        LOGGER.debug(settings)
        mode = settings.get('mode', 'color')
        if mode != self.mode:
            if not self.allow_switch_mode and self.mode is not None:
                self._reload_block()
                return
            self.mode = mode

        new_state = data.get(self.state_pos) == 1

        if self.mode == 'color':
            self.brightness = int(settings.get('gain', 0))
            self.white_value = int(settings.get('white', 0))
        else:
            self.brightness = int(settings.get('brightness', 0))

        self.rgb = [data.get(111), data.get(121), data.get(131)]

        self.temp = int(settings.get('temp', 0))

        self.effect = int(settings.get('effect', 0))

        values = {'mode': self.mode, 'brightness': self.brightness,
                  'rgb': self.rgb, 'temp': self.temp,
                  'white_value': self.white_value,
                  'effect': self.effect}

        self._update(new_state, values)

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        lights = status.get(STATUS_RESPONSE_LIGHTS)
        if lights:
            light = lights[self._channel]
            mode = light.get(STATUS_RESPONSE_LIGHTS_MODE, 'color')
            if mode != self.mode:
                if not self.allow_switch_mode and self.mode is not None:
                    self._reload_block()
                    return
            self.mode = mode
            if self.mode == 'color':
                self.brightness = int(light.get('gain', 0))
                self.white_value = int(light.get('white', 0))
                self.rgb = [int(light[STATUS_RESPONSE_LIGHTS_RED]),
                            int(light[STATUS_RESPONSE_LIGHTS_GREEN]),
                            int(light[STATUS_RESPONSE_LIGHTS_BLUE])]
            else:
                self.brightness = \
                    int(light.get(STATUS_RESPONSE_LIGHTS_BRIGHTNESS, 0))

            new_state = light.get(STATUS_RESPONSE_LIGHTS_STATE, None)
            values = {'mode': self.mode, 'brightness': self.brightness,
                      'rgb': self.rgb, 'temp': self.temp,
                      'white_value': self.white_value,
                      'effect': self.effect}
            self._update(new_state, values)

    def _send_data(self, state, brightness=None, rgb=None, temp=None,
                   mode=None, effect=None, white_value=None):
        url = self.url + "?"

        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                self._send_command(url)
                return

            url += "turn=on&"

        if mode is not None:
            self._send_command("/settings/?mode=" + mode)
        else:
            mode = self.mode

        if effect is not None:
            self._send_command("/color/0/?effect=" + str(effect))

        if brightness is not None:
            if mode == "white":
                url += "brightness=" + str(brightness) + "&"
            else:
                url += "gain=" + str(brightness) + "&"

        if white_value is not None:
            url += "white=" + str(white_value) + "&"

        if rgb is not None:
            url += "red=" + str(rgb[0]) + "&"
            url += "green=" + str(rgb[1]) + "&"
            url += "blue=" + str(rgb[2]) + "&"

        if temp is not None:
            url += "temp=" + str(temp) + "&"

        self._send_command(url)

    def turn_on(self, rgb=None, brightness=None, temp=None, mode=None,
                effect=None, white_value=None):
        self._send_data(True, brightness, rgb, temp, mode, effect, white_value)

    def set_values(self, rgb=None, brightness=None, temp=None, mode=None,
                   effect=None, white_value=None):
        self._send_data(None, brightness, rgb, temp, mode, effect, white_value)

    def turn_off(self):
        self._send_data(False)

    def get_dim_value(self):
        return self.brightness

    def set_dim_value(self, value):
        self._send_data(True, value)

    def get_white_value(self):
        return self.white_value

    def set_white_value(self, value):
        self._send_data(True, white_value=value)

class Bulb(Light):
    def __init__(self, block):
        super(Bulb, self).__init__(block, 181)
        self.effects_list = EFFECTS_BULB
        self.support_color_temp = True

class RGBWW(Light):
    def __init__(self, block):
        super(RGBWW, self).__init__(block, 151)
        self.support_color_temp = True

class RGBW2W(Light):
    def __init__(self, block, channel):
        super(RGBW2W, self).__init__(block, 161, channel)
        self.id = self.id + '-' + str(channel)
        self._channel = channel - 1
        self.mode = "white"
        self.url = "/white/" + str(channel - 1)
        self.effects_list = None
        self.allow_switch_mode = False

    def update(self, data):
        if 181 in data:
            new_state = data.get(151 + self._channel * 10) == 1
            self.brightness = data.get(111 + self._channel * 10)
            values = {'mode': self.mode, 'brightness': self.brightness}
                      #'rgb': self.rgb, 'temp': self.temp}
            self._update(new_state, values)
        else:
            self._reload_block()

class RGBW2C(Light):
    def __init__(self, block):
        super(RGBW2C, self).__init__(block, 161)
        self.mode = "color"
        self.url = "/color/0"
        self.effects_list = EFFECTS_RGBW2
        self.allow_switch_mode = False
        self.support_white_value = True
