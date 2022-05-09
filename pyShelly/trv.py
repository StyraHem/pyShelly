# -*- coding: utf-8 -*-
"""Shelly TRV"""

from keyword import kwlist
from .device import Device

from .const import (
    INFO_VALUE_TEMP,
    INFO_VALUE_TARGET_TEMP,
    INFO_VALUE_POSITION,
    ATTR_POS,
    ATTR_FMT,
    ATTR_PATH,
    ATTR_CHANNEL,
    ATTR_TOPIC,
    ATTR_RPC
)

class Trv(Device):
    def __init__(self, block):
        super(Trv, self).__init__(block)
        self.id = block.id
        self.state = None
        self.device_type = "TRV"
        self.is_sensor = True
        # self._state_cfg = {
        #     ATTR_POS: [112, 1101],
        #     ATTR_PATH: 'relays/$/ison',
        #     ATTR_FMT: 'bool',
        #     ATTR_TOPIC: 'relay/$',
        #     ATTR_RPC: 'switch:$/output'
        # }
        self._info_value_cfg = {
            #Todo add total used and returned 4106, 4107
            INFO_VALUE_TARGET_TEMP : {
                ATTR_POS: 3103,
                ATTR_PATH: 'thermostats/$/target_t/value',
                #ATTR_FMT: 'bool',
                #ATTR_TOPIC: 'input/$',
                #ATTR_RPC: 'input:$/state'
            },
            INFO_VALUE_TEMP : {
                ATTR_POS: 3101,
                ATTR_PATH: 'thermostats/$/tmp/value'                
            },
            INFO_VALUE_POSITION : {
                ATTR_POS: 3121,
                ATTR_PATH: 'thermostats/$/pos'                
            }
        }
        #     INFO_VALUE_OVER_POWER : {
        #         ATTR_POS: [6102],
        #         ATTR_PATH: 'relays/$/overpower',
        #         ATTR_FMT: 'bool',
        #         ATTR_RPC: 'switch:$/errors/include:overpower'
        #     },
        #     INFO_VALUE_OVER_VOLTAGE : {
        #         ATTR_RPC: 'switch:$/errors/include:overvoltage',
        #         ATTR_FMT: 'bool'
        #     }
        # }

    def update_coap(self, payload):
        #super().update_coap(payload)
        pass
        
    def update_status_information(self, status, src):
        #super().update_status_information(status, src)
        pass

    def update_mqtt(self, payload):
        pass

    def set_target_temp(self,temp):
        self._send_command(
            "/settings/thermostats/0?target_t=" + str(temp),
            "thermostat/0/command/target_t",  temp)
