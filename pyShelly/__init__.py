# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except, invalid-name

import base64
from datetime import datetime, timedelta
import json
import asyncio
import socket
import struct
import threading
import time

from .cloud import Cloud
from .block import Block
from .device import Device
from .utils import exception_log, timer
from .coap import CoAP
from .mdns import MDns
#from .device.relay import Relay
#from .device.switch import Switch
#from .device.powermeter import Po

from .utils import shelly_http_get
from .compat import s, b, ba2c
from .const import (
    LOGGER,
    VERSION,
    STATUS_RESPONSE_RELAYS,
    STATUS_RESPONSE_RELAY_OVER_POWER,
    STATUS_RESPONSE_RELAY_STATE,
    STATUS_RESPONSE_METERS,
    STATUS_RESPONSE_METERS_POWER,
    SENSOR_UNAVAILABLE_SEC,
    INFO_VALUE_RSSI,
    INFO_VALUE_UPTIME,
    INFO_VALUE_OVER_POWER,
    INFO_VALUE_DEVICE_TEMP,
    INFO_VALUE_OVER_TEMPERATURE,
    INFO_VALUE_SSID,
    INFO_VALUE_HAS_FIRMWARE_UPDATE,
    INFO_VALUE_LATEST_FIRMWARE_VERSION,
    INFO_VALUE_FW_VERSION,
    INFO_VALUE_CLOUD_STATUS,
    INFO_VALUE_CLOUD_ENABLED,
    INFO_VALUE_CLOUD_CONNECTED,
    INFO_VALUE_MQTT_CONNECTED,
    INFO_VALUE_CURRENT_CONSUMPTION,
    INFO_VALUE_SWITCH,
    INFO_VALUE_BATTERY,
    ATTR_PATH,
    ATTR_FMT,
    BLOCK_INFO_VALUES,
    SHELLY_TYPES,
    EFFECTS_RGBW2,
    EFFECTS_BULB
)

__version__ = VERSION

try:
    import http.client as httplib
except:
    import httplib

class pyShelly():
    def __init__(self):
        LOGGER.info("Init  %s", VERSION)
        self.stopped = threading.Event()
        self.blocks = {}
        self.devices = []
        self.cb_block_added = []
        self.cb_device_added = []
        self.cb_device_removed = []
        # Used if igmp packages not sent correctly
        self.igmp_fix_enabled = False
        self.mdns_enabled = False
        self.username = None
        self.password = None
        self.update_status_interval = None
        self._update_thread = None
        self._socket = None
        self.only_device_id = None
        self.tmpl_name = "{room} - {name}"

        self.cloud = None
        self.cloud_server = None
        self.cloud_auth_key = None

        self._coap = CoAP(self)
        self._mdns = None
        self.host_ip = ''

        self._shelly_by_ip = {}

        #self.loop = asyncio.get_event_loop()

        self._send_discovery_timer = timer(timedelta(seconds=60))
        self._check_by_ip_timer = timer(timedelta(seconds=60))

    def start(self):
        if self.mdns_enabled:
            self._mdns = MDns(self)
        if self.cloud_auth_key and self.cloud_server:
            self.cloud = Cloud(self, self.cloud_server, self.cloud_auth_key)
            self.cloud.start()
        if self._coap:
            self._coap.start()
        if self._mdns:
            self._mdns.start()
        #asyncio.ensure_future(self._update_loop())
        self._update_thread = threading.Thread(target=self._update_loop)
        self._update_thread.name = "Poll"
        self._update_thread.daemon = True
        self._update_thread.start()

    def version(self):
        return VERSION

    def close(self):
        if self.cloud:
            self.cloud.stop()
        self.stopped.set()
        if self._coap:
            self._coap.close()
        if self._mdns:
            self._mdns.close()
        if self._update_thread is not None:
            self._update_thread.join()
        if self._socket:
            self._socket.close()

    def discover(self):
        if self._coap:
            self._coap.discover()

    def add_device_by_ip(self, ip_addr, src):
        LOGGER.debug("Check add device by host %s %s", ip_addr, src)
        if ip_addr not in self._shelly_by_ip:
            LOGGER.debug("Add device by host %s %s", ip_addr, src)
            self._shelly_by_ip[ip_addr] = {'done':False, 'src':src,
                                           'poll_block':None}
        else:
            block = self._shelly_by_ip[ip_addr]['poll_block']
            if block:
                self._poll_block(block)

    def check_by_ip(self):
        for ip_addr in list(self._shelly_by_ip.keys()):
            data = self._shelly_by_ip[ip_addr]
            if not data['done']:
                done = False
                success, settings = shelly_http_get(
                    ip_addr, "/settings", self.username, self.password, False)
                if success:
                    success, status = shelly_http_get(
                        ip_addr, "/status", self.username, self.password, False)
                    if success:
                        done = True
                        self._shelly_by_ip[ip_addr]['done'] = True
                        dev = settings["device"]
                        device_id = dev["hostname"].rpartition('-')[2]
                        device_type = dev["type"]
                        ip_addr = status["wifi_sta"]["ip"]
                        LOGGER.debug("Add device from IP, %s, %s, %s",
                                     device_id, device_type, ip_addr)
                        self.update_block(device_id, device_type, ip_addr,
                                          self._shelly_by_ip[ip_addr]['src'],
                                          None)
                        if device_id in self.blocks:
                            block = self.blocks[device_id]
                            if block and block.sleep_device:
                                self._shelly_by_ip[ip_addr]['poll_block'] \
                                    = block
                if not done:
                    LOGGER.info("Error adding device, %s", ip_addr)

    def add_device(self, dev, discovery_src):
        LOGGER.debug('Add device')
        dev.discovery_src = discovery_src
        self.devices.append(dev)
        if not dev.lazy_load:
            self.callback_add_device(dev)

    def callback_add_device(self, dev):
        if hasattr(dev, 'discovery_src'):
            for callback in self.cb_device_added:
                dev.lazy_load = False
                callback(dev, dev.discovery_src)

    def remove_device(self, dev, discovery_src):
        LOGGER.debug('Remove device')
        self.devices.remove(dev)
        for callback in self.cb_device_removed:
            callback(dev, discovery_src)

    def update_block(self, block_id, device_type, ipaddr, src, payload):
        if self.only_device_id is not None and \
            block_id != self.only_device_id:
            return

        block_added = False
        if block_id not in self.blocks:
            block = self.blocks[block_id] = \
                Block(self, block_id, device_type, ipaddr, src)
            block_added = True

        block = self.blocks[block_id]

        if payload:
            data = {d[1]:d[2] for d in json.loads(payload)['G']}
            block.update(data, ipaddr)
            block.payload = payload

        if block_added:
            for callback in self.cb_block_added:
                callback(block)
            for device in block.devices:
                self.add_device(device, block.discovery_src)

        if block.sleep_device:
            self._poll_block(block)

    def _update_loop(self):
        LOGGER.debug("Start update loop, %s sec", self.update_status_interval)
        while not self.stopped.isSet():
            try:
                #LOGGER.debug("Checking blocks")
                if self._check_by_ip_timer.check():
                    self.check_by_ip()
                if self._send_discovery_timer.check():
                    self.discover()

                for key in list(self.blocks.keys()):
                    block = self.blocks[key]
                    #LOGGER.debug("Checking block, %s %s",
                    # block.id, block.last_update_status_info)

                    if not block.sleep_device:
                        self._poll_block(block)

                time.sleep(0.5)
            except Exception as ex:
                exception_log(ex, "Error update loop")

    def _poll_block(self, block):
        now = datetime.now()
        if self.update_status_interval is not None and \
            (block.last_update_status_info is None or \
            now - block.last_update_status_info \
                > self.update_status_interval):

            LOGGER.debug("Polling block, %s %s", block.id, block.type)
            block.last_update_status_info = now
            t = threading.Thread(
                target=block.update_status_information)
            t.daemon = True
            t.start()
