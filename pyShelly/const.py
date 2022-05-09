# -*- coding: utf-8 -*-

import logging

LOGGER = logging.getLogger('pyShelly')

NAME = "pyShelly"
VERSION = "1.0.2"

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

MDNS_IP = "224.0.0.251"
MDNS_PORT = 5353

#20210323-105928/v1.10.1-gf276b51
#20201019-110845/v1.6.6_4Pro@bad181e4
REGEX_VER = r"^20(\d{6}).+v(\d+\.\d+\.\d+(-rc\d)?)([^\d].*)?$"

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
STATUS_RESPONSE_INPUTS_EVENT = 'event'
STATUS_RESPONSE_INPUTS_EVENT_CNT = 'event_cnt'

STATUS_RESPONSE_LIGHTS = 'lights'
STATUS_RESPONSE_LIGHTS_STATE = 'ison'
STATUS_RESPONSE_LIGHTS_BRIGHTNESS = 'brightness'
STATUS_RESPONSE_LIGHTS_WHITE = 'white'
STATUS_RESPONSE_LIGHTS_MODE = 'mode'
STATUS_RESPONSE_LIGHTS_RED = 'red'
STATUS_RESPONSE_LIGHTS_GREEN = 'green'
STATUS_RESPONSE_LIGHTS_BLUE = 'blue'
STATUS_RESPONSE_LIGHTS_POWER = 'power'

STATUS_RESPONSE_ROLLERS = 'rollers'
STATUS_RESPONSE_ROLLERS_STATE = 'state'
STATUS_RESPONSE_ROLLERS_LAST_DIR = 'last_direction'
STATUS_RESPONSE_ROLLERS_POSITION = 'current_pos'
STATUS_RESPONSE_ROLLERS_POWER = 'power'
STATUS_RESPONSE_ROLLERS_TOTAL = 'total'

SENSOR_UNAVAILABLE_SEC = 3600 * 13 #13 hours

INFO_VALUE_RSSI = 'rssi'
INFO_VALUE_RSSI_LEVEL = 'rssi_level'
INFO_VALUE_UPTIME = 'uptime'
INFO_VALUE_OVER_POWER = 'over_power'
INFO_VALUE_OVER_VOLTAGE = 'over_voltage'
INFO_VALUE_DEVICE_TEMP = 'device_temp'
INFO_VALUE_OVER_TEMPERATURE = 'over_temp'
INFO_VALUE_SSID = 'ssid'
INFO_VALUE_HAS_FIRMWARE_UPDATE = 'has_firmware_update'
INFO_VALUE_LATEST_FIRMWARE_VERSION = 'latest_fw_version'
INFO_VALUE_LATEST_BETA_FW_VERSION = 'latest_beta_fw_version'
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
INFO_VALUE_TILT = 'tilt'
INFO_VALUE_VIBRATION = 'vibration'
INFO_VALUE_TEMP = 'temperature'
INFO_VALUE_HUMIDITY = 'humidity'
INFO_VALUE_ILLUMINANCE = 'illuminance'
INFO_VALUE_GAS = 'gas'
INFO_VALUE_SENSOR = 'sensor'
INFO_VALUE_TOTAL_WORK_TIME = 'total_work_time'
INFO_VALUE_TARGET_TEMP = 'target_temperature'
INFO_VALUE_POSITION = 'position'

ATTR_PATH = 'path'
ATTR_FMT = 'fmt'
ATTR_POS = 'pos'
ATTR_CHANNEL = 'channel'
ATTR_AUTO_SET = 'auto_set'
ATTR_TOPIC = 'topic'
ATTR_RPC = 'rpc'

SRC_COAP = 1
SRC_STATUS = 2
SRC_MQTT = 3
SRC_MQTT_STATUS = 4
SRC_RPC = 5
SRC_WS = 6
SRC_WS_STATUS = 7

BLOCK_INFO_VALUES = {
    INFO_VALUE_SSID : {ATTR_PATH :'wifi_sta/ssid', ATTR_RPC:'wifi:ssid'},
    INFO_VALUE_RSSI : {ATTR_PATH : 'wifi_sta/rssi', ATTR_RPC:'wifi/rssi'},
    INFO_VALUE_UPTIME : {ATTR_PATH : 'uptime', ATTR_RPC:'sys/uptime'},
    INFO_VALUE_DEVICE_TEMP : {ATTR_PATH : 'tmp/tC', ATTR_POS: [311, 3104], ATTR_TOPIC: 'temperature', ATTR_RPC:'switch:$/temperature/tC'}, #, ATTR_FMT : 'round'},
    INFO_VALUE_OVER_TEMPERATURE : {ATTR_PATH : 'overtemperature', ATTR_POS: 6101, ATTR_TOPIC: 'overtemperature', ATTR_RPC: 'switch:$/errors/include:overtemp'},
    INFO_VALUE_HAS_FIRMWARE_UPDATE : {ATTR_PATH : 'update/has_update'},
    INFO_VALUE_LATEST_FIRMWARE_VERSION : {ATTR_PATH : 'update/new_version',
                                          ATTR_FMT : 'ver'},
    INFO_VALUE_FW_VERSION : {ATTR_PATH : 'update/old_version',
                             ATTR_FMT : 'ver'},
    INFO_VALUE_CLOUD_ENABLED : {ATTR_PATH : 'cloud/enabled', ATTR_RPC : 'cloud/enable'}, #ed remover 220428
    INFO_VALUE_CLOUD_CONNECTED : {ATTR_PATH : 'cloud/connected', ATTR_RPC : 'cloud/connected'},
    INFO_VALUE_MQTT_CONNECTED : {ATTR_PATH : 'mqtt/connected', ATTR_RPC : 'mqtt/connected'},
    #INFO_VALUE_CURRENT_CONSUMPTION : {ATTR_PATH : 'consumption'},
    INFO_VALUE_VOLTAGE : {ATTR_PATH : 'voltage', ATTR_FMT : 'round', ATTR_RPC : 'switch:$/voltage'},
    INFO_VALUE_BATTERY : {ATTR_PATH : 'bat/value', ATTR_POS : [77, 3111], ATTR_TOPIC: "sensor/battery"},
    #INFO_VALUE_TILT : {ATTR_PATH : 'accel/tilt'}, #Todo
    #INFO_VALUE_VIBRATION : {ATTR_PATH : 'accel/vibration'}, #Todo
    #INFO_VALUE_TEMP : {ATTR_PATH : 'tmp/tC'},
    #INFO_VALUE_ILLUMINANCE : {ATTR_PATH : 'lux/value'}, #Todo
    INFO_VALUE_GAS : {ATTR_PATH : 'concentration/ppm'},
    INFO_VALUE_SENSOR : {ATTR_PATH : 'gas_sensor/sensor_state'},
    INFO_VALUE_TOTAL_WORK_TIME : {ATTR_PATH : 'total_work_time'},
}

SHELLY_TYPES = {
    'SHSW-1': {'name': "Shelly 1", 'mqtt':'shelly1'},
    'SHSW-21': {'name': "Shelly 2", 'mqtt':'shellyswitch'},
    'SHSW-22': {'name': "Shelly HD Pro"},
    'SHSW-25': {'name': "Shelly 2.5", 'mqtt':'shellyswitch25'},
    'SHSW-44': {'name': "Shelly 4 Pro", 'mqtt':'shelly4pro'},
    'SHPLG-1': {'name': "Shelly Plug", 'mqtt':'shellyplug'},
    'SHPLG2-1': {'name': "Shelly Plug"},
    'SHPLG-S': {'name': "Shelly Plug S", 'mqtt':'shellyplug-s'},
    'SHRGBWW-01': {'name': "Shelly RGBWW"},
    'SHBLB-1': {'name': "Shelly Bulb", 'mqtt':'shellybulb'},
    'SHCB-1': {'name': "Shelly Bulb", 'mqtt':'shellycolorbulb'},
    'SHHT-1': {'name': "Shelly H&T", 'battery' : True, 'mqtt':'shellyht'},
    'SHRGBW2': {'name': "Shelly RGBW2", 'mqtt':'shellyrgbw2'},
    'SHEM': {'name': "Shelly EM", 'mqtt':'shellyem'},
    'SHEM-3': {'name': "Shelly 3EM", 'mqtt':'shellyem3'},
    'SHCL-255': {'name': "Shelly Bulb"},
    'SH2LED-1': {'name': "Shelly 2LED"},
    'SHSK-1': {'name': "Shelly Socket"},
    'SHSW-PM': {'name': "Shelly 1 PM", 'mqtt':'shelly1pm'},
    'SHWT-1': {'name': "Shelly Flood", 'battery' : True, 'mqtt':'shellyflood'},
    'SHDM-1': {'name': "Shelly Dimmer", 'mqtt':'shellydimmer'},
    'SHDM-2': {'name': "Shelly Dimmer 2", 'mqtt':'shellydimmer2'},
    'SHDW-1': {'name': "Shelly Door/Window", 'battery' : True,
               'mqtt':'shellydw'},
    'SHDW-2': {'name': "Shelly Door/Window 2", 'battery' : True,
               'mqtt':'shellydw2'},
    'SHBDUO-1': {'name': "Shelly Duo", 'mqtt':'ShellyBulbDuo'},
    'SHVIN-1': {'name': "Shelly Vintage", 'mqtt':'ShellyVintage'},
    'SHBTN-1': {'name': "Shelly Button 1", 'mqtt':'shellybutton1', 'battery' : True},
    'SHBTN-2': {'name': "Shelly Button 1", 'battery' : True},
    'SHIX3-1': {'name': "Shelly i3", 'mqtt':'shellyix3'},
    'SHGS-1': {'name': "Shelly Gas", 'mqtt':'shellygas'},
    'SHAIR-1': {'name': "Shelly Air", 'mqtt':'ShellyAir'},
    'SHPLG-U1': {'name': "Shelly Plug US", 'mqtt':'shellyplugu1'},
    'SHUNI-1': {'name': "Shelly UNI", 'mqtt':'shellyuni'},
    'SHSW-L': {'name': "Shelly 1L", 'mqtt':'shelly1l'},
    'SHMOS-01': {'name': "Shelly Motion", 'mqtt':'shellymotionsensor'},
    'ShellyPlus1': {'name':"Shelly Plus 1", 'mqtt':'shellyplus1'},
    'ShellyPlus1PM': {'name':"Shelly Plus 1PM", 'mqtt':'shellyplus1pm'},    
    'ShellyPlus2': {'name':"Shelly Plus 2", 'mqtt':'shellyplus2'},
    'ShellyPlus2PM': {'name':"Shelly Plus 2PM", 'mqtt':'shellyplus2pm'},
    'ShellyPro1': {'name':"Shelly Pro 1", 'mqtt':'shellypro1'},
    'ShellyPro1PM': {'name':"Shelly Pro 1PM", 'mqtt':'shellypro1pm'},
    'ShellyPro2': {'name':"Shelly Pro 2", 'mqtt':'shellypro2'},
    'ShellyPro2PM': {'name':"Shelly Pro 2PM", 'mqtt':'shellypro2pm'},
    'ShellyPro4PM': {'name':"Shelly Pro 4PM", 'mqtt':'shellypro4pm'},
    'ShellyPlusI4': {'name':"Shelly Plus i4", 'mqtt':'shellyplusi4'},
    'SHTRV-01': {'name':"Shelly TRV", 'mqtt':'shellytrv'},
    #'SNSN-0013A': {'name': "Shelly Plus H&T", 'mqtt':'shellyplusht'}
}

EFFECTS_RGBW2 = [
    {'name': "Off", 'effect': 0},
    {'name': "Meteor shower", 'effect': 1},
    {'name': "Gradual change", 'effect': 2},
    {'name': "Flash", 'effect': 3}
]

EFFECTS_BULB = [
    {'name': "Off", 'effect': 0},
    {'name': "Meteor shower", 'effect': 1},
    {'name': "Gradual change", 'effect': 2},
    {'name': "Breath", 'effect': 3},
    {'name': "Flash", 'effect': 4},
    {'name': "On/off gradual", 'effect': 5},
    {'name': "Red/green change", 'effect': 6},
]

RSSI_LEVELS = {
    -50 : "excelent",
    -60 : "very good",
    -70 : "good",
    -1000: "weak"
}

