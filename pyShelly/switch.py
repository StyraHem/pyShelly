# -*- coding: utf-8 -*-

from .device import Device
from .utils import notNone
from threading import Timer
from datetime import datetime
from .const import (
    LOGGER,
    STATUS_RESPONSE_INPUTS,
    STATUS_RESPONSE_INPUTS_INPUT,
    STATUS_RESPONSE_INPUTS_EVENT,
    STATUS_RESPONSE_INPUTS_EVENT_CNT,
    SRC_COAP, SRC_STATUS
)

class Switch(Device):
    """Class to represent a power meter value"""
    def __init__(self, block, channel, 
                 position=None, simulate_state=False, master_unit=False):
        super(Switch, self).__init__(block)
        self.id = block.id
        self.master_unit = master_unit
        if channel > 0: #Todo: Move to base
            self.id += "-" + str(channel)
            self._channel = channel - 1
            self.device_nr = channel
        else:
            self._channel = 0
        self._position = notNone(position, [118, 2101])
        self._event_pos = [119, 2102]
        self._event_cnt_pos = [120, 2103]
        #if self._event_pos and type(self._event_pos) is not list:
        #    self._event_pos = [self._event_pos]
        #self._event_cnt_pos = event_cnt_pos
        self._simulate_state = simulate_state
        #self.sensor_values = {}
        self.device_type = "SWITCH"
        self.last_event = None
        self.event_cnt = None
        self.battery_bug_fix = False
        self.hold_delay = None #bug fix

    def update_coap(self, payload):
        """Get the power"""
        state = self.coap_get(payload, self._position)
        event_cnt = self.coap_get(payload, self._event_cnt_pos)
        self.battery_bug_fix = (self.coap_get(payload, [3112]) == 0 and event_cnt == 1)
        if self.battery_bug_fix:
            if self.hold_delay:
                diff = datetime.now() - self.hold_delay
                if diff.total_seconds() <= 10:
                    return
            self.hold_delay = datetime.now()
            event_cnt = (self.event_cnt or 0) + 1
            self.hold = True
        if not event_cnt is None and self.event_cnt != event_cnt:
            if self._simulate_state and self.event_cnt is not None:
                state = 1
                self.timer = Timer(1,self._turn_off)
                self.timer.start()
            self.last_event = self.coap_get(payload, self._event_pos)
            self.event_cnt = event_cnt
        if not state is None:
            state = bool(state)
        self._update(SRC_COAP, state, {'last_event' : self.last_event,
                                  'event_cnt' : self.event_cnt})

    def update_status_information(self, status):
        """Update the status information."""
        new_state = None
        if not self.battery_bug_fix:
            inputs = status.get(STATUS_RESPONSE_INPUTS)
            if inputs:
                value = inputs[self._channel]
                new_state = value.get(STATUS_RESPONSE_INPUTS_INPUT, None) != 0
                event_cnt = value.get(STATUS_RESPONSE_INPUTS_EVENT_CNT, None)
                if not event_cnt is None and self.event_cnt != event_cnt:
                    if self._simulate_state and self.event_cnt is not None:
                        new_state = True
                        self.timer = Timer(1,self._turn_off)
                        self.timer.start()
                    self.last_event = value.get(STATUS_RESPONSE_INPUTS_EVENT, None)
                    self.event_cnt = event_cnt
        self._update(SRC_STATUS, new_state, {'last_event' : self.last_event,
                                         'event_cnt' : self.event_cnt})

    def _turn_off(self):
        self._update(None, False)
        self.raise_updated()
