# -*- coding: utf-8 -*-

from threading import Timer

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

        self.kg_last_event = ""
        self.kg_last_event_cnt = None
        self.kg_last_state = None
        self.kg_click_count = 0
        self.kg_click_timer = None
        self.kg_send_event_events = ""
        self.kg_send_event_click_count = 0
        self.kg_start_state = None
        self.kg_momentary_button = False

    def kg_send_event(self):
        if self.kg_momentary_button:
            self.kg_send_event_events = self.kg_last_event
            self.kg_send_event_click_count = 0
        else:    
            self.kg_send_event_events = ""
            self.kg_send_event_click_count = self.kg_click_count

        self.kg_last_event = ""
        self.kg_click_count = 0

        self.raise_updated(True)


    def update_coap(self, payload):
        """Get the power"""
#   Start state                   Action           CoAP
#   -----------------------------------------------------------------------------------------------------------
#       0                                          [0,2101,0],[0,2102," "],[0,2103,42]
#                                 1 Fast click     [0,2101,0],[0,2102,"S"],[0,2103,43]
#
#       0                                          [0,2101,0],[0,2102," "],[0,2103,43] 
#                                 1 Normal click   [0,2101,1],[0,2102," "],[0,2103,43]
#                                                  [0,2101,0],[0,2102,"S"],[0,2103,44]
#
#       0                                          [0,2101,0],[0,2102," "],[0,2103,45]
#                                 2 Fast click     [0,2101,0],[0,2102,"S"],[0,2103,47]
#
#       0                                          [0,2101,0],[0,2102," "],[0,2103,461]
#                                 1 Long click     [0,2101,1],[0,2102," "],[0,2103,461]
#                                 slow             [0,2101,1],[0,2102,"L"],[0,2103,462]
#                                                  [0,2101,0],[0,2102," "],[0,2103,462]
#
#       0                                          [0,2101,0],[0,2102," "],[0,2103,67]
#                                 1 Long click     [0,2101,1],[0,2102," "],[0,2103,67]
#                                 fast             [0,2101,0],[0,2102,"L"],[0,2103,68]
#
#       1                                          [0,2101,1],[0,2102," "],[0,2103,74]     
#                                 1 Fast click     [0,2101,1],[0,2102," "],[0,2103,74] 
#                                                  [0,2101,1],[0,2102,"L"],[0,2103,75]
#
#       1                                          [0,2101,1],[0,2102," "],[0,2103,466]
#                                 1 Normal click   [0,2101,0],[0,2102," "],[0,2103,466] 
#                                                  [0,2101,1],[0,2102," "],[0,2103,466]
#                                                  [0,2101,1],[0,2102,"L"],[0,2103,467]

        kg_curr_state = self.coap_get(payload, self._position)
        kg_curr_event = self.coap_get(payload, self._event_pos)
        kg_curr_event_cnt = self.coap_get(payload, self._event_cnt_pos)
        if not kg_curr_event_cnt is None:
            if not self.kg_last_event_cnt is None and not self.kg_last_state is None:
                if kg_curr_event_cnt != self.kg_last_event_cnt:
                    if not self.kg_click_timer is None:
                        self.kg_click_timer.cancel()
                        self.kg_click_timer = None
                        
                    if kg_curr_event == "S":
                        if self.kg_last_state == 1:
                            self.kg_click_count += 1
                        else:    
                            self.kg_click_count += 2
                        if kg_curr_state == 1:
                            self.kg_click_count += 1

                        if kg_curr_event_cnt - self.kg_last_event_cnt > 1:
                            self.kg_click_count += (kg_curr_event_cnt - self.kg_last_event_cnt - 1) * 2
                            kg_curr_event = "S"*(kg_curr_event_cnt - self.kg_last_event_cnt)

                    if kg_curr_event == "L":
                        if self.kg_momentary_button:
                            if kg_curr_state != self.kg_last_state:
                                self.kg_click_count += 1
                            self.kg_send_event_events = self.kg_last_event + "LSTART"
                            self.kg_send_event_click_count = 0
                            self.raise_updated(True)
                        else:        
                            if self.kg_last_state == 0:
                                self.kg_click_count += 1
                            else:    
                                self.kg_click_count += 2

                            if kg_curr_state == 0:
                                self.kg_click_count += 1

                            if kg_curr_event_cnt - self.kg_last_event_cnt > 1:
                                self.kg_click_count += (kg_curr_event_cnt - self.kg_last_event_cnt - 1) * 2

                    self.kg_last_event += kg_curr_event

                    if not self.kg_momentary_button or kg_curr_state == 0:
                        self.kg_click_timer = Timer(0.7, self.kg_send_event)
                        self.kg_click_timer.start()

                if kg_curr_event_cnt == self.kg_last_event_cnt and kg_curr_state != self.kg_last_state:
                    if not self.kg_click_timer is None:
                        self.kg_click_timer.cancel()
                        self.kg_click_timer = None

                    self.kg_click_count += 1

                    if self.kg_momentary_button and kg_curr_state == 0 and len(self.kg_last_event) > 0:
                        if self.kg_last_event[-1] == "L":
                            self.kg_send_event_events = self.kg_last_event + "STOP"
                            self.kg_send_event_click_count = 0
                            self.raise_updated(True)

                    if not self.kg_momentary_button or kg_curr_state == 0:
                        self.kg_click_timer = Timer(0.7, self.kg_send_event)
                        self.kg_click_timer.start()

            self.kg_last_state = kg_curr_state            
            self.kg_last_event_cnt = kg_curr_event_cnt

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
