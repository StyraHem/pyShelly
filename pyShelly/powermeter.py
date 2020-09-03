# -*- coding: utf-8 -*-

from .device import Device
from .utils import notNone
from .const import (
    #LOGGER,
    STATUS_RESPONSE_METERS,
    STATUS_RESPONSE_EMETERS,
    STATUS_RESPONSE_METERS_POWER,
    STATUS_RESPONSE_METERS_TOTAL,
    STATUS_RESPONSE_METERS_VOLTAGE,
    STATUS_RESPONSE_METERS_PF,
    STATUS_RESPONSE_METERS_CURRENT,
    STATUS_RESPONSE_METERS_TOTAL_RETURNED,
    INFO_VALUE_CURRENT_CONSUMPTION,
    INFO_VALUE_TOTAL_CONSUMPTION,
    INFO_VALUE_TOTAL_RETURNED,
    INFO_VALUE_VOLTAGE,
    INFO_VALUE_POWER_FACTOR,
    INFO_VALUE_CURRENT,
    ATTR_POS,
    ATTR_PATH,
    ATTR_FMT
)

class PowerMeter(Device):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, position = None,
                 tot_pos = None, voltage_to_block=False, em=False):
        #Todo: voltage_to_block
        super(PowerMeter, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
            self.device_nr = channel
        else:
            self._channel = 0
        # if meters is None:
        #     self.meters = [self._channel]
        # else:
        #     self.meters = meters
        #self.sensor_values = {}
        self.device_type = "POWERMETER"
        self.info_values = {}
        self.state = None
        self._state_cfg = {
            ATTR_POS: notNone(position, [111, 4101, 4102, 4105]),
            ATTR_PATH: 'meters/$/power',
            ATTR_FMT: ['float']
        }
        meters = "emeters" if em else "meters"
        divider = None if em else '/60'
        self._info_value_cfg = {
            INFO_VALUE_VOLTAGE : {
                ATTR_POS: [116, 4108],
                ATTR_PATH: meters + '/$/voltage',
                ATTR_FMT: ['float']
            },
            INFO_VALUE_POWER_FACTOR : {
                ATTR_POS: [114, 4110],
                ATTR_PATH: meters + 'eters/$/pf',
                ATTR_FMT: ['float']
            },
            INFO_VALUE_CURRENT : {
                ATTR_POS: [115, 4109],
                ATTR_PATH: meters + '/$/current',
                ATTR_FMT: ['float']
            },
            INFO_VALUE_TOTAL_CONSUMPTION : {
                ATTR_POS: tot_pos or [4103, 4104, 4106],
                ATTR_PATH: meters + '/$/total',
                ATTR_FMT: ['float', divider, 'round:2']
            },
            INFO_VALUE_TOTAL_RETURNED :
            {
                ATTR_POS: [4107],
                ATTR_PATH: meters + '/$/total_returned',
                ATTR_FMT: ['float', divider, 'round:2']
            }
        }

    # """
    # def update_status_information(self, status):
    #     ""Update the status information.""
    #      factor = 1
    #     if STATUS_RESPONSE_EMETERS in status:
    #         meters = status.get(STATUS_RESPONSE_EMETERS) #Shelly EM
    #     else:
    #         meters = status.get(STATUS_RESPONSE_METERS)
    #         factor = 60
    #     if meters:
    #         power = 0
    #         total = None
    #         total_returned = None
    #         for meterpos in self.meters:
    #             meter = meters[meterpos]
    #             if meter.get(STATUS_RESPONSE_METERS_POWER) is not None:
    #                 power += float(meter.get(STATUS_RESPONSE_METERS_POWER))
    #             if meter.get(STATUS_RESPONSE_METERS_TOTAL) is not None:
    #                 total = (total or 0) + \
    #                     float(meter.get(STATUS_RESPONSE_METERS_TOTAL))
    #             if meter.get(STATUS_RESPONSE_METERS_TOTAL_RETURNED) is not None:
    #                 total_returned = (total_returned or 0) + \
    #                     float(meter.get(STATUS_RESPONSE_METERS_TOTAL_RETURNED))
    #             if meter.get(STATUS_RESPONSE_METERS_VOLTAGE) is not None:
    #                 if self._voltage_to_block:
    #                     self.block.info_values[INFO_VALUE_VOLTAGE] = \
    #                         float(meter.get(STATUS_RESPONSE_METERS_VOLTAGE))
    #                 else:
    #                     self.info_values[INFO_VALUE_VOLTAGE] = \
    #                         float(meter.get(STATUS_RESPONSE_METERS_VOLTAGE))
    #             elif status.get(STATUS_RESPONSE_METERS_VOLTAGE) is not None:
    #                 #Fix for Shelly 2.5 etc
    #                 self.block.info_values[INFO_VALUE_VOLTAGE] = \
    #                     float(status.get(STATUS_RESPONSE_METERS_VOLTAGE))
    #             if meter.get(STATUS_RESPONSE_METERS_PF) is not None:
    #                 self.info_values[INFO_VALUE_POWER_FACTOR] = \
    #                     float(meter.get(STATUS_RESPONSE_METERS_PF))
    #             if meter.get(STATUS_RESPONSE_METERS_CURRENT) is not None:
    #                 self.info_values[INFO_VALUE_CURRENT] = \
    #                     float(meter.get(STATUS_RESPONSE_METERS_CURRENT))
    #         self.state = power
    #         if total_returned is not None:
    #             self.info_values[INFO_VALUE_TOTAL_RETURNED] \
    #                 = round(total_returned / factor)
    #         if total is not None:
    #             self.info_values[INFO_VALUE_TOTAL_CONSUMPTION] \
    #                 = round(total / factor)
    #         self._update(self.state, info_values=self.info_values) """

    # def update_coap(self, payload):
    #     """Get the power"""
    #     update = False
    #     if self._positions:
    #         self.state = sum(payload.get(pos, 0) for pos in self._positions)
    #         update = True
    #     """ 
    #     if self._volt_pos and self._volt_pos in payload:
    #         update = True
    #         if self._voltage_to_block:
    #             self.block.info_values[INFO_VALUE_VOLTAGE] = \
    #                 round(payload[self._volt_pos], 2)
    #         else:
    #             self.info_values[INFO_VALUE_VOLTAGE] = \
    #                 round(payload[self._volt_pos], 2)
    #     if self._pf_pos and self._pf_pos in payload:
    #         update = True
    #         self.info_values[INFO_VALUE_POWER_FACTOR] = \
    #             round(payload[self._pf_pos], 2)
    #     if self._current_pos and self._current_pos in payload:
    #         update = True
    #         self.info_values[INFO_VALUE_CURRENT] = \
    #             round(payload[self._current_pos], 2)
    #     if self._tot_pos and self._tot_pos in payload:
    #         update = True
    #         self.info_values[INFO_VALUE_TOTAL_CONSUMPTION] = \
    #             round(payload[self._tot_pos]/60)
    #     if update:
    #         self._update(self.state, info_values=self.info_values) """