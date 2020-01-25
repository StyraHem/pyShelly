# -*- coding: utf-8 -*-

from .device import Device
from .const import (
    #LOGGER,
    STATUS_RESPONSE_METERS,
    STATUS_RESPONSE_EMETERS,
    STATUS_RESPONSE_METERS_POWER,
    STATUS_RESPONSE_METERS_TOTAL,
    INFO_VALUE_CURRENT_CONSUMPTION,
    INFO_VALUE_TOTAL_CONSUMPTION
)

class PowerMeter(Device):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, positions, meters=None):
        super(PowerMeter, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
            self.device_nr = channel
        else:
            self._channel = 0
        if meters is None:
            self.meters = [self._channel]
        else:
            self.meters = meters
        self._positions = positions
        self.sensor_values = {}
        self.device_type = "POWERMETER"
        self.info_values = {}
        self.state = None

    def update_status_information(self, status):
        """Update the status information."""
        if STATUS_RESPONSE_EMETERS in status:
            meters = status.get(STATUS_RESPONSE_EMETERS) #Shelly EM
        else:
            meters = status.get(STATUS_RESPONSE_METERS)
        if meters:
            power = 0
            total = 0
            for meterpos in self.meters:
                meter = meters[meterpos]
                if meter.get(STATUS_RESPONSE_METERS_POWER) is not None:
                    power += float(meter.get(STATUS_RESPONSE_METERS_POWER))
                if meter.get(STATUS_RESPONSE_METERS_TOTAL) is not None:
                    total += float(meter.get(STATUS_RESPONSE_METERS_TOTAL))
            self.state = power
            self.info_values[INFO_VALUE_TOTAL_CONSUMPTION] \
                = round(total / 60, 2)
            self._update(self.state, info_values=self.info_values)

    def update(self, data):
        """Get the power"""
        if self._positions:
            self.state = sum(data.get(pos, 0) for pos in self._positions)
            self._update(self.state)