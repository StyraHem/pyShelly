# -*- coding: utf-8 -*-

from .device import Device
from threading import Timer
from .const import (
    STATUS_RESPONSE_INPUTS,
    STATUS_RESPONSE_INPUTS_INPUT,
    STATUS_RESPONSE_INPUTS_EVENT,
    STATUS_RESPONSE_INPUTS_EVENT_CNT
)

class Switch(Device):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, position,
                 event_pos=None, event_cnt_pos=None, simulate_state=False):
        super(Switch, self).__init__(block)
        self.id = block.id
        if channel > 0:
            self.id += "-" + str(channel)
            self._channel = channel - 1
            self.device_nr = channel
        else:
            self._channel = 0
        self._position = position
        self._event_pos = event_pos
        self._event_cnt_pos = event_cnt_pos
        self._simulate_state = simulate_state
        self.sensor_values = {}
        self.device_type = "SWITCH"
        self.last_event = None
        self.event_cnt = None

    def update(self, data):
        """Get the power"""
        state = data.get(self._position)
        if self._event_pos:
            self.last_event = data.get(self._event_pos)
            event_cnt = data.get(self._event_cnt_pos)
            if self.event_cnt and self.event_cnt != event_cnt:
                self.event_cnt = event_cnt
                if self._simulate_state:
                    state = True
                    self.timer = Timer(1,self._turn_off)
                    self.timer.start()
        self._update(state > 0, {'last_event' : self.last_event,
                                 'event_cnt' : self.event_cnt})

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        inputs = status.get(STATUS_RESPONSE_INPUTS)
        if inputs:
            value = inputs[self._channel]
            new_state = value.get(STATUS_RESPONSE_INPUTS_INPUT, None)
            self.last_event = value.get(STATUS_RESPONSE_INPUTS_EVENT, None)
            event_cnt = value.get(STATUS_RESPONSE_INPUTS_EVENT_CNT, None)
            if self.event_cnt != event_cnt:
                self.event_cnt = event_cnt
                if self._simulate_state:
                    new_state = True
                    self.timer = Timer(1,self._turn_off)
                    self.timer.start()
            self._update(new_state > 0, {'last_event' : self.last_event,
                                         'event_cnt' : self.event_cnt})

    def _turn_off(self):
        self._update(False)
