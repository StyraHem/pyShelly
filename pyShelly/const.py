# -*- coding: utf-8 -*-

import logging

LOGGER = logging.getLogger('pyShelly')

NAME = "pyShelly"
VERSION = "0.1.20"

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

MDNS_IP = "224.0.0.251"
MDNS_PORT = 5353

"""Define constants for result from /status response from device"""
STATUS_RESPONSE_RELAYS = 'relays'
STATUS_RESPONSE_RELAY_OVER_POWER = 'overpower'
STATUS_RESPONSE_RELAY_STATE = 'ison'

STATUS_RESPONSE_METERS = 'meters'
STATUS_RESPONSE_METERS_POWER = 'power'
STATUS_RESPONSE_METERS_TOTAL = 'total'
STATUS_RESPONSE_METERS_VOLTAGE = 'voltage'
STATUS_RESPONSE_METERS_PF = 'pf'
STATUS_RESPONSE_METERS_CURRENT = 'current'
STATUS_RESPONSE_METERS_TOTAL_RETURNED = 'total_returned'

STATUS_RESPONSE_EMETERS = 'emeters'

STATUS_RESPONSE_INPUTS = 'inputs'
STATUS_RESPONSE_INPUTS_INPUT = 'input'

STATUS_RESPONSE_LIGHTS = 'lights'
STATUS_RESPONSE_LIGHTS_STATE = 'ison'
STATUS_RESPONSE_LIGHTS_BRIGHTNESS = 'brightness'
STATUS_RESPONSE_LIGHTS_WHITE = 'white'
STATUS_RESPONSE_LIGHTS_MODE = 'mode'
STATUS_RESPONSE_LIGHTS_RED = 'red'
STATUS_RESPONSE_LIGHTS_GREEN = 'green'
STATUS_RESPONSE_LIGHTS_BLUE = 'blue'

STATUS_RESPONSE_ROLLERS = 'rollers'
STATUS_RESPONSE_ROLLERS_STATE = 'state'
STATUS_RESPONSE_ROLLERS_LAST_DIR = 'last_direction'
STATUS_RESPONSE_ROLLERS_POSITION = 'current_pos'
STATUS_RESPONSE_ROLLERS_POWER = 'power'

SENSOR_UNAVAILABLE_SEC = 3600 * 13 #13 hours

INFO_VALUE_RSSI = 'rssi'
INFO_VALUE_UPTIME = 'uptime'
INFO_VALUE_OVER_POWER = 'over_power'
INFO_VALUE_DEVICE_TEMP = 'device_temp'
INFO_VALUE_OVER_TEMPERATURE = 'over_temp'
INFO_VALUE_SSID = 'ssid'
INFO_VALUE_HAS_FIRMWARE_UPDATE = 'has_firmware_update'
INFO_VALUE_LATEST_FIRMWARE_VERSION = 'latest_fw_version'
INFO_VALUE_FW_VERSION = 'firmware_version'
INFO_VALUE_CLOUD_STATUS = 'cloud_status'
INFO_VALUE_CLOUD_ENABLED = 'cloud_enabled'
INFO_VALUE_CLOUD_CONNECTED = 'cloud_connected'
INFO_VALUE_MQTT_CONNECTED = 'mqtt_connected'
INFO_VALUE_CURRENT_CONSUMPTION = 'current_consumption'
INFO_VALUE_SWITCH = 'switch'
INFO_VALUE_BATTERY = 'battery'
INFO_VALUE_PAYLOAD = 'payload'
INFO_VALUE_TOTAL_CONSUMPTION = 'total_consumption'
INFO_VALUE_TOTAL_RETURNED = 'total_returned'
INFO_VALUE_VOLTAGE = 'voltage'
INFO_VALUE_POWER_FACTOR = 'power_factor'
INFO_VALUE_CURRENT = 'current'

ATTR_PATH = 'path'
ATTR_FMT = 'fmt'

BLOCK_INFO_VALUES = {
    INFO_VALUE_SSID : {ATTR_PATH :'wifi_sta/ssid'},
    INFO_VALUE_RSSI : {ATTR_PATH : 'wifi_sta/rssi'},
    INFO_VALUE_UPTIME : {ATTR_PATH : 'uptime'},
    INFO_VALUE_DEVICE_TEMP : {ATTR_PATH : 'tmp/tC', ATTR_FMT : 'round'},
    INFO_VALUE_OVER_TEMPERATURE : {ATTR_PATH : 'overtemperature'},
    INFO_VALUE_HAS_FIRMWARE_UPDATE : {ATTR_PATH : 'update/has_update'},
    INFO_VALUE_LATEST_FIRMWARE_VERSION : {ATTR_PATH : 'update/new_version'},
    INFO_VALUE_FW_VERSION : {ATTR_PATH : 'update/old_version'},
    INFO_VALUE_CLOUD_ENABLED : {ATTR_PATH : 'cloud/enabled'},
    INFO_VALUE_CLOUD_CONNECTED : {ATTR_PATH : 'cloud/connected'},
    INFO_VALUE_MQTT_CONNECTED : {ATTR_PATH : 'mqtt/connected'},
    #INFO_VALUE_CURRENT_CONSUMPTION : {ATTR_PATH : 'consumption'},
    #INFO_VALUE_VOLTAGE : {ATTR_PATH : 'voltage', ATTR_FMT : 'round'},
    INFO_VALUE_BATTERY : {ATTR_PATH : 'bat/value'}
}

SHELLY_TYPES = {
    'SHSW-1': {'name': "Shelly 1"},
    'SHSW-21': {'name': "Shelly 2"},
    'SHSW-22': {'name': "Shelly HD Pro"},
    'SHSW-25': {'name': "Shelly 2.5"},
    'SHSW-44': {'name': "Shelly 4 Pro"},
    'SHPLG-1': {'name': "Shelly Plug"},
    'SHPLG2-1': {'name': "Shelly Plug"},
    'SHPLG-S': {'name': "Shelly Plug S"},
    'SHRGBWW-01': {'name': "Shelly RGBWW"},
    'SHBLB-1': {'name': "Shelly Bulb"},
    'SHHT-1': {'name': "Shelly H&T", 'battery' : True},
    'SHRGBW2': {'name': "Shelly RGBW2"},
    'SHEM': {'name': "Shelly EM"},
    'SHEM-3': {'name': "Shelly 3EM"},
    'SHCL-255': {'name': "Shelly Bulb"},
    'SH2LED-1': {'name': "Shelly 2LED"},
    'SHSK-1': {'name': "Shelly Socket"},
    'SHSW-PM': {'name': "Shelly 1 PM"},
    'SHWT-1': {'name': "Shelly Flood", 'battery' : True},
    'SHDM-1': {'name': "Shelly Dimmer"},
    'SHDW-1': {'name': "Shelly Door/Window", 'battery' : True},
}

EFFECTS_RGBW2 = [
    {'name': "Off", 'effect': 0},
    {'name': "Meteor shower", 'effect': 1},
    {'name':"Gradual change", 'effect': 2},
    {'name': "Flash", 'effect': 3}
]

EFFECTS_BULB = [
    {'name': "Off", 'effect': 0},
    {'name': "Meteor shower", 'effect': 1},
    {'name': "Gradual change", 'effect': 2},
    {'name':"Breath", 'effect': 3},
    {'name':"Flash", 'effect': 4},
    {'name': "On/off gradual", 'effect': 5},
    {'name':"Red/green change", 'effect': 6},
]
