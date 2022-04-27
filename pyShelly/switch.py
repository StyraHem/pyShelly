# -*- coding: utf-8 -*-

from .device import Device
from .utils import notNone
from threading import Timer
from datetime import datetime
import json
from .const import (
    LOGGER,
    STATUS_RESPONSE_INPUTS,
    STATUS_RESPONSE_INPUTS_INPUT,
    STATUS_RESPONSE_INPUTS_EVENT,
    STATUS_RESPONSE_INPUTS_EVENT_CNT,
    SRC_COAP, SRC_STATUS, SRC_MQTT,
    ATTR_POS, ATTR_PATH, ATTR_FMT, ATTR_TOPIC, ATTR_RPC
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
        self._simulate_state = simulate_state
        self.device_type = "SWITCH"
        self.last_event = None
        self.event_cnt = None
        #self.battery_bug_fix = False
        self.hold_delay = None #bug fix
        self.hold_event_cnt = None
        self.battery = False

    def __update(self, state, event_cnt, last_event, src):
        if self.battery:
            if self.hold_delay and self.hold_event_cnt == event_cnt:
                diff = datetime.now() - self.hold_delay
                if diff.total_seconds() <= 10:
                    return
            self.hold_delay = datetime.now()
            self.hold_event_cnt = event_cnt
            event_cnt = (self.event_cnt or 0) + 1
        if not event_cnt is None and self.event_cnt != event_cnt:
            if self._simulate_state and self.event_cnt is not None:
                state = 1
                self.timer = Timer(1, self._turn_off)
                self.timer.start()
            self.last_event = last_event
            self.event_cnt = event_cnt
        if not state is None:
            state = bool(state)
        self._update(src, state, {'last_event' : self.last_event,
                                  'event_cnt' : self.event_cnt})

    def rpc_event(self, comp, type):
        state = None
        if comp=='input:' + str(self._channel):
            if type == "btn_down":
                state = True
            if type == "btn_up":
                state = False
            #if type == "single_push":
        if state != None:
            self.__update(state, None, None, SRC_MQTT)

    def update_rpc(self, rpc_data, src):
        state = self._get_rpc_value({ATTR_RPC:'input:$/state'}, rpc_data)
        self.__update(state, None, None, SRC_MQTT)

    def update_mqtt(self, payload):
        if payload['topic'] == "input_event/" + str(self._channel):
            data = json.loads(payload['data'])
            event = data["event"]
            event_cnt = data["event_cnt"]
            self.__update(None, event_cnt, event, SRC_MQTT)

    def update_coap(self, payload):
        """Get the power"""
        state = self.coap_get(payload, self._position)
        event_cnt = self.coap_get(payload, self._event_cnt_pos)
        self.battery = self.coap_get(payload, [3112]) == 0
        last_event = self.coap_get(payload, self._event_pos)
        self.__update(state, event_cnt, last_event, SRC_COAP)

    def update_status_information(self, status, src):
        """Update the status information."""
        new_state = None
        inputs = status.get(STATUS_RESPONSE_INPUTS)
        if inputs:
            value = inputs[self._channel]
            new_state = value.get(STATUS_RESPONSE_INPUTS_INPUT, None) != 0
            self._update(src, new_state)

    def _turn_off(self):
        self._update(None, False)
        self.raise_updated()
