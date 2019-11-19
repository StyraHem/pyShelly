# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except, invalid-name

import base64
from datetime import datetime, timedelta
import json
import socket
import struct
import threading
import time

from .cloud import Cloud
from .block import Block
from .device import Device
from .utils import exception_log
#from .device.relay import Relay
#from .device.switch import Switch
#from .device.powermeter import Po

from .utils import shelly_http_get
from .compat import s, b, ba2c
from .const import (
    LOGGER,
    VERSION,
    COAP_IP,
    COAP_PORT,
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
    INFO_VALUE_CONSUMPTION,
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
        self.username = None
        self.password = None
        self.update_status_interval = None
        self._coap_thread = None
        self._update_thread = None
        self._socket = None
        self.only_device_id = None

    def open(self):
        self.init_socket()
        self._coap_thread = threading.Thread(target=self._coap_loop)
        self._coap_thread.name = "CoAP"
        self._coap_thread.daemon = True
        self._coap_thread.start()
        self._update_thread = threading.Thread(target=self._update_loop)
        self._update_thread.name = "Poll"
        self._update_thread.daemon = True
        self._update_thread.start()

    def version(self):
        return VERSION

    def init_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                          socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
        sock.bind(('', COAP_PORT))
        mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP),
                           socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(15)
        self._socket = sock

    def close(self):
        self.stopped.set()
        if self._coap_thread is not None:
            self._coap_thread.join()
        if self._update_thread is not None:
            self._update_thread.join()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self._socket.close()

    def discover(self):
        LOGGER.debug("Sending discover UDP")
        msg = bytes(b'\x50\x01\x00\x0A\xb3cit\x01d\xFF')
        self._socket.sendto(msg, (COAP_IP, COAP_PORT))

    def add_device_by_host(self, host, device_id):
        success, res = shelly_http_get(host, "/settings", self.username, self.password)
        if success:
            dev = res["device"]
            device_type = dev["type"]
            #id = dev["mac"][6:]
            self._update_block(device_id, device_type,
                               host, 'by_host', None)

    def add_device(self, dev, code):
        LOGGER.debug('Add device')
        self.devices.append(dev)
        for callback in self.cb_device_added:
            callback(dev, code)

    def remove_device(self, dev, code):
        LOGGER.debug('Remove device')
        self.devices.remove(dev)
        for callback in self.cb_device_removed:
            callback(dev, code)

    def _update_block(self, block_id, device_type, ipaddr, code, payload):
        block_added = False
        if block_id not in self.blocks:
            block = self.blocks[block_id] = \
                Block(self, block_id, device_type, ipaddr, code)
            block_added = True

        block = self.blocks[block_id]

        if payload:
            data = {d[1]:d[2] for d in json.loads(payload)['G']}
            block.update(data, ipaddr)

        if block_added:
            for callback in self.cb_block_added:
                callback(block)
            for device in block.devices:
                self.add_device(device, block.code)

    def _update_loop(self):

        LOGGER.info("Start update loop, %s sec", self.update_status_interval)
        while not self.stopped.isSet():
            try:
                any_hit = False
                LOGGER.debug("Checking blocks")
                #self.discover() #todo
                for key in list(self.blocks.keys()):
                    block = self.blocks[key]
                    LOGGER.debug("Checking block, %s %s", block.id, block.last_update_status_info)
                    if self.update_status_interval is not None and \
                        (block.last_update_status_info is None or \
                        datetime.now() - block.last_update_status_info \
                            > self.update_status_interval):
                        any_hit = True
                        LOGGER.debug("Polling block, %s %s", block.id, block.type)
                        #todo ??
                        #t = threading.Thread(
                        #    target=block.update_status_information) 
                        #t.daemon = True
                        #t.start()
                        try:
                            block.update_status_information()
                        except Exception as ex:
                            exception_log(ex, "Error update block status")
                if not any_hit:
                    time.sleep(0.5)
            except Exception as ex:
                exception_log(ex, "Error update loop")


    def _coap_loop(self):

        next_igmp_fix = datetime.now() + timedelta(minutes=1)

        while not self.stopped.isSet():

            try:

                # This fix is needed if not sending IGMP reports correct
                if self.igmp_fix_enabled and datetime.now() > next_igmp_fix:
                    LOGGER.debug("IGMP fix")
                    next_igmp_fix = datetime.now() + timedelta(minutes=1)
                    mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP),
                                       socket.INADDR_ANY)
                    try:
                        self._socket.setsockopt(socket.IPPROTO_IP,
                                                socket.IP_DROP_MEMBERSHIP,
                                                mreq)
                    except Exception as e:
                        LOGGER.debug("Can't drop membership, %s", e)
                    try:
                        self._socket.setsockopt(socket.IPPROTO_IP,
                                                socket.IP_ADD_MEMBERSHIP, mreq)
                    except Exception as e:
                        LOGGER.debug("Can't add membership, %s", e)

                #LOGGER.debug("Wait for UDP message")

                try:
                    data_tmp, addr = self._socket.recvfrom(1024)
                except socket.timeout:
                    continue

                ipaddr = addr[0]

                #LOGGER.debug("Got UDP message")

                data = bytearray(data_tmp)
                LOGGER.debug("CoAP msg: %s %s", ipaddr, data_tmp)

                pos = 0

                #Receice messages with ip from proxy
                if data[0] == 112 and data[1] == 114 \
                   and data[2] == 120 and data[3] == 121:
                    ipaddr = socket.inet_ntoa(data[4:8])
                    pos = 8

                byte = data[pos]
                #ver = byte >> 6
                #typex = (byte >> 4) & 0x3
                #tokenlen = byte & 0xF

                code = data[pos+1]
                #msgid = 256 * data[2] + data[3]
                LOGGER.debug("CoAP msg: %s %s %s", code, ipaddr, data)

                pos = pos + 4

                #LOGGER.debug(' Code: %s', code)

                if code == 30 or code == 69:

                    byte = data[pos]
                    tot_delta = 0

                    device_type = ''
                    device_id = ''

                    while byte != 0xFF:
                        delta = byte >> 4
                        length = byte & 0x0F

                        if delta == 13:
                            pos = pos + 1
                            delta = data[pos] + 13
                        elif delta == 14:
                            pos = pos + 2
                            delta = data[pos - 1] * 256 + data[pos] + 269

                        tot_delta = tot_delta + delta

                        if length == 13:
                            pos = pos + 1
                            length = data[pos] + 13
                        elif length == 14:
                            pos = pos + 2
                            length = data[pos - 1] * 256 + data[pos] + 269

                        value = data[pos + 1:pos + length]
                        pos = pos + length + 1

                        if tot_delta == 3332:
                            device_type, device_id, _ = s(value).split('#', 2)

                        byte = data[pos]

                    payload = s(data[pos + 1:])

                    if self.only_device_id is not None and \
                            device_id != self.only_device_id:
                        continue

                    LOGGER.debug('CoAP Code: %s, Type %s, Id %s, Payload *%s*', code, device_type,
                                  device_id, payload.replace(' ', ''))

                    if code == 30:
                        self._update_block(device_id, device_type,
                                           ipaddr, code, None) #payload)

                    if code == 69:
                        self._update_block(device_id, device_type,
                                           ipaddr, code, None)

            except Exception as ex:
                exception_log(ex, "Error receiving UDP")
