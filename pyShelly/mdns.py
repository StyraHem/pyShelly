# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except, invalid-name

import threading
from datetime import datetime, timedelta
import socket
import struct
import time
import re

from .utils import exception_log
from .const import (
    LOGGER,
    MDNS_IP,
    MDNS_PORT
)

class MDns():

    def __init__(self, root):
        self._root = root
        self._thread = threading.Thread(target=self._loop)
        self._thread.name = "mDns"
        self._thread.daemon = True
        self._socket = None

    def start(self):
        self._init_socket()
        self._thread.start()

    def _init_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
        sock.bind((self._root.host_ip, MDNS_PORT))
        if self._root.host_ip:
            mreq = struct.pack("=4s4s",
                               socket.inet_aton(MDNS_IP),
                               socket.inet_aton(self._root.host_ip))
        else:
            mreq = struct.pack("=4sl",
                               socket.inet_aton(MDNS_IP),
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

        time.sleep(10)  #Just wait some sec to get names from cloud etc

        next_igmp_fix = datetime.now() + timedelta(minutes=1)

        while not self._root.stopped.isSet():

            try:

                # This fix is needed if not sending IGMP reports correct
                if self._root.igmp_fix_enabled and \
                        datetime.now() > next_igmp_fix:
                    LOGGER.debug("IGMP fix")
                    next_igmp_fix = datetime.now() + timedelta(minutes=1)
                    mreq = struct.pack("=4sl", socket.inet_aton(MDNS_IP),
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

                try:
                    data_tmp, addr = self._socket.recvfrom(1024)
                except socket.timeout:
                    continue

                if len(data_tmp) < 5:
                    continue

                ipaddr = addr[0]

                data = bytearray(data_tmp)

                # id = data[0]
                # flags = data[1]
                #question = data[2]
                answer = data[3]
                #authority = data[4]
                #additional = data[5]

                if (answer > 0):
                    LOGGER.debug("mDns msg: %s %s", ipaddr, data_tmp)
                    p = re.compile(b'shelly(?P<type>[a-z0-9-]+)-(?P<id>[A-F0-9]{6,12})\x05')
                    m = p.search(data_tmp)
                    if m:
                        LOGGER.debug("mDns match Shelly")
                        #, m.group('id')
                        self._root.add_device_by_ip(ipaddr, "mDns")

            except Exception as ex:
                pass
                #exception_log(ex, "Error receiving mDns UDP")
