# -*- coding: utf-8 -*-
import json
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
    STATUS_RESPONSE_LIGHTS_POWER,
    INFO_VALUE_CURRENT_CONSUMPTION,
    INFO_VALUE_TOTAL_CONSUMPTION,
    #INFO_VALUE_SWITCH,
    ATTR_POS,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_TOPIC,
    SRC_COAP, SRC_STATUS, SRC_MQTT
)

class Light(Device):
    def __init__(self, block):
        super(Light, self).__init__(block)

class LightWhite(Light):
    def __init__(self, block, channel, state_pos, bright_pos, 
                 temp_pos=None, power_pos=None):
        super(LightWhite, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "LIGHT"
        self.url = "/light/0"
        if channel>0:
            self.id += "-" + str(channel)
            self._channel = channel-1
        else:
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

        self._info_value_cfg = {
            # INFO_VALUE_SWITCH : { #Only one...
            #     ATTR_POS: [118, 2101],
            #     ATTR_PATH: 'inputs/$/input',
            #     ATTR_FMT: 'bool'
            # },
            INFO_VALUE_CURRENT_CONSUMPTION : {
                    ATTR_POS: power_pos or [141, 4101],
                    ATTR_PATH: 'meters/$/power',
                    ATTR_FMT: ['float'],
                    ATTR_TOPIC: 'white/$/power'
            },
            INFO_VALUE_TOTAL_CONSUMPTION : {
                ATTR_POS: [214, 4103],
                ATTR_PATH: 'meters/$/total',
                ATTR_FMT: ['float','/60','round:2'],
                ATTR_TOPIC: 'white/$/energy'
            }
        }

    def update_mqtt(self, payload):
        """Get the power"""
        if payload['topic'] == "white/" + str(self._channel) + '/status':
            status =  json.loads(payload['data'])
            new_state = status['ison']
            self.brightness = status['brightness']
            values = {'brightness': self.brightness, "color_temp": self.color_temp}
            self._update(SRC_MQTT, new_state, values)

    def update_coap(self, payload):
        new_state = self.coap_get(payload, self.state_pos) == 1
        bright = self.coap_get(payload, self.bright_pos)
        if bright is not None:
            self.brightness = int(bright)
        color_temp = self.coap_get(payload, self.temp_pos)
        if color_temp is not None:
            self.color_temp = int(color_temp)

        values = {'brightness': self.brightness, "color_temp": self.color_temp}

        self._update(SRC_COAP, new_state, values)

    def update_status_information(self, status, src):
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
            self._update(src, new_state, values)

    def _send_data(self, state, brightness=None, color_temp=None):
        url = self.url + "?"
        topic = 'white/' + str(self._channel) + '/set'
        payload = {}

        if state is not None:
            if not state or brightness == 0:
                url += "turn=off"
                payload['turn']='off'
                self._send_command(url, topic, payload)
                return
            url += "turn=on&"
            payload['turn']='on'

        if brightness is not None:
            url += "brightness=" + str(brightness) + "&"
            payload['brightness']=str(brightness)

        if color_temp is not None:
            url += "temp=" + str(color_temp) + "&"
            payload['temp']=str(color_temp)

        self._send_command(url, topic, payload)

    def turn_on(self, brightness=None, color_temp=None):
        self._send_data(True, brightness, color_temp)

    def set_values(self, state=None, brightness=None, color_temp=None, **kwargs):
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

class LightRGB(Light):
    def __init__(self, block, state_pos, channel=0, power_pos=None):
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
        self.power_pos = power_pos
        if channel>0:
            self.id += "-" + str(channel)
            self._channel = channel-1
        else:
            self._channel = 0
        self.info_values = {}
        self._info_value_cfg = {
            # INFO_VALUE_SWITCH : {
            #     ATTR_POS: [118, 2101],
            #     ATTR_PATH: 'inputs/$/input',
            #     ATTR_FMT: 'bool'
            # },
            INFO_VALUE_CURRENT_CONSUMPTION : {
                    ATTR_POS: power_pos or [141, 4101],
                    ATTR_PATH: 'meters/$/power',
                    ATTR_FMT: ['float']
            },
            INFO_VALUE_TOTAL_CONSUMPTION : {
                ATTR_POS: [4103],
                ATTR_PATH: 'meters/$/total',
                ATTR_FMT: ['float','/60','round:2']
            }
        }

    def update_mqtt(self, payload):
        if payload['topic'] == "color/" + str(self._channel) + '/status':
            status =  json.loads(payload['data'])
            new_state = status['ison']

            self.mode = status['mode']
            
            if self.mode == 'color':
                self.brightness = int(status.get('gain', 0))
                self.white_value = int(status.get('white', 0))
                self.rgb = [int(status.get('red')),
                            int(status.get('green')),
                            int(status.get('blue'))]
            
            self.effect = int(status.get('effect', 0))
            self.color_temp = int(status.get('temp', 0)) #???

            values = {'mode': self.mode, 'brightness': self.brightness,
                  'rgb': self.rgb, 'color_temp': self.color_temp,
                  'white_value': self.white_value,
                  'effect': self.effect}
            self._update(SRC_MQTT, new_state, values)

    def update_coap(self, payload):
        if not 9101 in payload:
            success, settings = self.block.http_get(self.url) #todo
            if not success:
                return
            self.mode = settings.get('mode', 'color')

            if self.mode == 'color':
                self.brightness = int(settings.get('gain', 0))
                self.white_value = int(settings.get('white', 0))
            else:
                self.brightness = int(settings.get('brightness', 0))

            self.color_temp = int(settings.get('temp', 0))
            self.effect = int(settings.get('effect', 0))

        else: #1.8.0
            self.mode = self.coap_get(payload, 9101)
            if self.mode == 'color':
                self.brightness = int(self.coap_get(payload, 5102))
            else:
                self.brightness = int(self.coap_get(payload, 5101))
            self.white_value = int(self.coap_get(payload, 5108))
            #Todo:self.color_temp = int(settings.get('temp', 0))

        #Todo
        # if mode != self.mode:
        #     if not self.allow_switch_mode and self.mode is not None:
        #         self._reload_block()
        #         return

        new_state = self.coap_get(payload, self.state_pos) == 1

        self.rgb = [self.coap_get(payload, [111, 5105]),
                    self.coap_get(payload, [121, 5106]),
                    self.coap_get(payload, [131, 5107])]

        # switch = self.coap_get(payload, [118, 2101])
        # if switch is not None:
        #     self.info_values['switch'] = switch > 0

        # power = self.coap_get(payload, [111, 5105])
        # if self.power_pos and self.power_pos in payload:
        #     self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] \
        #         = self.coap_get(payload, self.power_pos)

        values = {'mode': self.mode, 'brightness': self.brightness,
                  'rgb': self.rgb, 'color_temp': self.color_temp,
                  'white_value': self.white_value,
                  'effect': self.effect}

        self._update(SRC_COAP, new_state, values)

    def update_status_information(self, status, src):
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

            # if STATUS_RESPONSE_LIGHTS_POWER in light:
            #     self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] \
            #         = light[STATUS_RESPONSE_LIGHTS_POWER]

            new_state = light.get(STATUS_RESPONSE_LIGHTS_STATE, None)
            values = {'mode': self.mode, 'brightness': self.brightness,
                      'rgb': self.rgb, 'color_temp': self.color_temp,
                      'white_value': self.white_value,
                      'effect': self.effect}
            self._update(src, new_state, values)

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
                   effect=None, white_value=None, **kwargs):
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
        super(Bulb, self).__init__(block, [1101, 181])
        self.effects_list = EFFECTS_BULB
        self.support_color_temp = True

class RGBWW(LightRGB):
    def __init__(self, block):
        super(RGBWW, self).__init__(block, 151)
        self.support_color_temp = True

class RGBW2W(LightWhite):
    def __init__(self, block, channel):
        super(RGBW2W, self).__init__(block, channel, [161, 1101], [111, 5101],
                                     power_pos=[201, 4101])
        #self.id = self.id + '-' + str(channel)
        self.mode = "white"
        self.url = "/white/" + str(channel - 1)
        self.effects_list = None
        self.allow_switch_mode = False

    # def update_coap(self, payload):
    #     if 181 in payload:
    #         new_state = self.coap_get(payload, [151]) == 1
    #         self.brightness = self.coap_get(payload, [111])
    #         # if 118 in payload:
    #         #     self.info_values['switch'] = self.coap_get(payload, 118) > 0
    #         # if self.power_pos and self.power_pos in payload:
    #         #     self.info_values[INFO_VALUE_CURRENT_CONSUMPTION] \
    #         #         = self.coap_get(payload, self.power_pos)
    #         values = {'mode': self.mode, 'brightness': self.brightness}
    #                   #'rgb': self.rgb, 'temp': self.temp}
    #         self._update(new_state, values, None, self.info_values)
    #     else:
    #         self._reload_block()

class RGBW2C(LightRGB):
    def __init__(self, block):
        super(RGBW2C, self).__init__(block, [161, 1101], 0, [211, 4101])
        self.mode = "color"
        self.url = "/color/0"
        self.effects_list = EFFECTS_RGBW2
        self.allow_switch_mode = False
        self.support_white_value = True

class Duo(LightWhite):
    def __init__(self, block):
        super(Duo, self).__init__(block, 0, [121, 1101], [111, 5101], [131, 5103])
        self.support_color_temp = True
        self._color_temp_min = 2700
        self._color_temp_max = 6500
        self.is_sensor = True

class Vintage(LightWhite):
    def __init__(self, block):
        super(Vintage, self).__init__(block, 0, [121, 1101], [111, 5101])
        self.is_sensor = True
