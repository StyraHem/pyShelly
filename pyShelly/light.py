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
    STATUS_RESPONSE_LIGHTS_MODE,
    #STATUS_RESPONSE_INPUTS,
    #STATUS_RESPONSE_INPUTS_INPUT,
    #INFO_VALUE_SWITCH
)

class LightWhite(Device):
    def __init__(self, block, state_pos, bright_pos, temp_pos):
        super(LightWhite, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "LIGHT"
        self.url = "/light/0"

        self._channel = 0
        self.brightness = None
        self.color_temp = None

        self.state_pos = state_pos
        self.bright_pos = bright_pos
        self.temp_pos = temp_pos
        self.info_values = {}

        self.support_color_temp = False
        self._color_temp_min = None
        self._color_temp_max = None


    def update(self, data):
        self.state = data.get(self.state_pos) == 1
        if self.bright_pos and self.bright_pos in data:
            self.brightness = int(data.get(self.bright_pos))
        if self.temp_pos and self.temp_pos in data:
            self.color_temp = int(data.get(self.temp_pos))

        values = {'brightness': self.brightness, "color_temp": self.color_temp}

        self._update(self.state, values, None, self.info_values)

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        lights = status.get(STATUS_RESPONSE_LIGHTS)
        if lights:
            light = lights[self._channel]
            #self.brightness = int(light.get('gain', 0))
            self.brightness = \
                int(light.get(STATUS_RESPONSE_LIGHTS_BRIGHTNESS, 0))
            self.color_temp = int(light.get('temp', 0))
            new_state = light.get(STATUS_RESPONSE_LIGHTS_STATE, None)
            values = {'color_temp': self.color_temp, 'brightness': self.brightness}
            self._update(new_state, values, None, self.info_values)

    def _send_data(self, state, brightness=None, color_temp=None):
        url = self.url + "?"

        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                self._send_command(url)
                return
            url += "turn=on&"

        if brightness is not None:
            url += "brightness=" + str(brightness) + "&"

        if color_temp is not None:
            url += "temp=" + str(color_temp) + "&"

        self._send_command(url)

    def turn_on(self, brightness=None, color_temp=None):
        self._send_data(True, brightness, color_temp)

    def set_values(self, state=None, brightness=None, color_temp=None):
        self._send_data(state, brightness, color_temp)

    def turn_off(self):
        self._send_data(False)

    def get_dim_value(self):
        return self.brightness

    def set_dim_value(self, value):
        self._send_data(True, value)

    def get_color_temp_value(self):
        return self.color_temp

    def set_color_temp_value(self, value):
        self._send_data(True, color_temp=value)

class LightRGB(Device):
    def __init__(self, block, state_pos, channel=0):
        super(LightRGB, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "RGBLIGHT"
        self.url = "/light/0"

        self.mode = None
        self.brightness = None
        self.white_value = None
        self.rgb = None
        self.color_temp = None
        self.effect = None

        self.effects_list = None
        self.allow_switch_mode = True
        self.support_color_temp = False
        self.support_white_value = False

        self.state_pos = state_pos
        self._channel = channel
        self.info_values = {}

    def update(self, data):
        success, settings = self.block.http_get(self.url) #todo
        if not success:
            return

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

        self.color_temp = int(settings.get('temp', 0))

        self.effect = int(settings.get('effect', 0))

        if 118 in data:
            self.info_values['switch'] = data.get(118) > 0

        values = {'mode': self.mode, 'brightness': self.brightness,
                  'rgb': self.rgb, 'color_temp': self.color_temp,
                  'white_value': self.white_value,
                  'effect': self.effect}

        self._update(new_state, values, None, self.info_values)

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

            self.color_temp = int(light.get('temp', 0))

            self.effect = int(light.get('effect', 0))

            new_state = light.get(STATUS_RESPONSE_LIGHTS_STATE, None)
            values = {'mode': self.mode, 'brightness': self.brightness,
                      'rgb': self.rgb, 'color_temp': self.color_temp,
                      'white_value': self.white_value,
                      'effect': self.effect}
            self._update(new_state, values, None, self.info_values)

    def _send_data(self, state, brightness=None, rgb=None, color_temp=None,
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

        if color_temp is not None:
            url += "temp=" + str(color_temp) + "&"

        self._send_command(url)

    def turn_on(self, rgb=None, brightness=None, color_temp=None, mode=None,
                effect=None, white_value=None):
        self._send_data(True, brightness, rgb,
                        color_temp, mode, effect, white_value)

    def set_values(self, rgb=None, brightness=None, color_temp=None, mode=None,
                   effect=None, white_value=None):
        self._send_data(None, brightness, rgb,
                        color_temp, mode, effect, white_value)

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

class Bulb(LightRGB):
    def __init__(self, block):
        super(Bulb, self).__init__(block, 181)
        self.effects_list = EFFECTS_BULB
        self.support_color_temp = True

class RGBWW(LightRGB):
    def __init__(self, block):
        super(RGBWW, self).__init__(block, 151)
        self.support_color_temp = True

class RGBW2W(LightRGB):
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
            if 118 in data:
                self.info_values['switch'] = data.get(118) > 0
            values = {'mode': self.mode, 'brightness': self.brightness}
                      #'rgb': self.rgb, 'temp': self.temp}
            self._update(new_state, values, None, self.info_values)
        else:
            self._reload_block()

class RGBW2C(LightRGB):
    def __init__(self, block):
        super(RGBW2C, self).__init__(block, 161)
        self.mode = "color"
        self.url = "/color/0"
        self.effects_list = EFFECTS_RGBW2
        self.allow_switch_mode = False
        self.support_white_value = True

class Duo(LightWhite):
    def __init__(self, block):
        super(Duo, self).__init__(block, 121, 111, 131)
        self.support_color_temp = True
        self._color_temp_min = 2700
        self._color_temp_max = 6500
