# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except, invalid-name

import threading
from datetime import datetime, timedelta
import time
import socket
import struct

from .compat import s
from .utils import exception_log
from .const import (
    LOGGER,
    COAP_IP,
    COAP_PORT
)
class CoAP():

    def __init__(self, root):
        self._root = root
        self._thread = threading.Thread(target=self._loop)
        self._thread.name = "CoAP"
        self._thread.daemon = True
        self._socket = None

    def start(self):
        try:
            self._init_socket()
            self._thread.start()
        except:
            LOGGER.exception("Can't setup CoAP listener")

    def discover(self):
        if self._socket:
            LOGGER.debug("Sending CoAP discover UDP")
            msg = bytes(b'\x50\x01\x00\x0A\xb3cit\x01d\xFF')
            self._socket.sendto(msg, (COAP_IP, COAP_PORT))

    def _init_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
        sock.bind((self._root.bind_ip, COAP_PORT))
        if self._root.host_ip:
            mreq = struct.pack("=4s4s",
                               socket.inet_aton(COAP_IP),
                               socket.inet_aton(self._root.host_ip))
        else:
            mreq = struct.pack("=4sl",
                               socket.inet_aton(COAP_IP),
                               socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(15)
        self._socket = sock

    def close(self):
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

    def _loop(self):

        self._root.stopped.wait(10)
        #Just wait some sec to get names from cloud etc

        next_igmp_fix = datetime.now() + timedelta(minutes=1)

        while not self._root.stopped.isSet():

            try:
                # This fix is needed if not sending IGMP reports correct
                if self._root.igmp_fix_enabled and \
                        datetime.now() > next_igmp_fix:
                    LOGGER.debug("IGMP fix")
                    next_igmp_fix = datetime.now() + timedelta(minutes=1)
                    if self._root.host_ip:
                        mreq = struct.pack("=4s4s",
                               socket.inet_aton(COAP_IP),
                               socket.inet_aton(self._root.host_ip))
                    else:
                        mreq = struct.pack("=4sl",
                               socket.inet_aton(COAP_IP),
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

                #todo add auto discover??

                #LOGGER.debug("Wait for UDP message")

                try:
                    data_tmp, addr = self._socket.recvfrom(1024)
                except socket.timeout:
                    continue

                ipaddr = addr[0]

                #LOGGER.debug("Got UDP message")

                data = bytearray(data_tmp)
                LOGGER.debug("CoAP msg: %s", ipaddr) #, data_tmp)

                if len(data) < 10:
                    continue

                pos = 0

                #Receice messages with ip from proxy
                if data[0] == 112 and data[1] == 114 \
                   and data[2] == 120 and data[3] == 121:
                    ipaddr = socket.inet_ntoa(data[4:8])
                    pos = 8

                byte = data[pos]
                tkl = byte & 0x0F
                #ver = byte >> 6
                #typex = (byte >> 4) & 0x3
                #tokenlen = byte & 0xF

                code = data[pos+1]
                #msgid = 256 * data[2] + data[3]
                LOGGER.debug("CoAP msg: %s %s", code, ipaddr) #, data)

                pos = pos + 4 + tkl

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

                    try:
                        payload = s(data[pos + 1:])
                    except:
                        LOGGER.info(data)

                    if payload: #Fix for DW2 payload error
                        payload = payload.replace(",,",",").replace("][", "],[")

                    LOGGER.debug('CoAP Code: %s, Type %s, Id %s, Payload *%s*', code, device_type, device_id, payload.replace(' ', ''))

                    if code == 30:
                        self._root.update_block(device_id, device_type,
                                           ipaddr, 'CoAP-msg', payload)

                    if code == 69:
                        self._root.update_block(device_id, device_type,
                                           ipaddr, 'CoAP-discovery', None)

            except Exception as ex:
                #LOGGER.debug("Error receive CoAP %s", str(ex))
                LOGGER.exception("Error receive CoAP")
                #exception_log(ex, "Error receiving CoAP UDP")
