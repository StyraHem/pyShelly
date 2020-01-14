# -*- coding: utf-8 -*-

from .device import Device
from .const import (
    #LOGGER,
    STATUS_RESPONSE_METERS,
    STATUS_RESPONSE_METERS_POWER,
    INFO_VALUE_CONSUMPTION
)

class PowerMeter(Device):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, positions):
        super(PowerMeter, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
        else:
            self._channel = 0
        self._positions = positions
        self.sensor_values = {}
        self.device_type = "POWERMETER"

    def update_status_information(self, status):
        """Update the status information."""
        info_values = {}
        meters = status.get(STATUS_RESPONSE_METERS)
        if meters:
            meter = meters[self._channel]
            if meter.get(STATUS_RESPONSE_METERS_POWER) is not None:
                info_values[INFO_VALUE_CONSUMPTION] = \
                    meter.get(STATUS_RESPONSE_METERS_POWER)
            self._update(None, None, info_values)

    def update(self, data):
        """Get the power"""
        if self._positions:
            consumption = sum(data.get(pos, 0) for pos in self._positions)
            self._update(None, None, {INFO_VALUE_CONSUMPTION: consumption})