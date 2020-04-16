# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except, invalid-name

import re
import ipaddress
from zeroconf import ( ServiceBrowser, Zeroconf )

MATCH_NAME = re.compile("(?P<name>shelly.+)-(?P<id>[0-9A-F]+)._http._tcp.local.")

class MDns:

    def remove_service(self, _zeroconf, type, name):
        pass

    def add_service(self, zeroconf, type, name):
        test = MATCH_NAME.fullmatch(name)
        if test:
            info = zeroconf.get_service_info(type, name)
            for addr in info.addresses:
                ipaddr = str(ipaddress.IPv4Address(addr))
                self._root.add_device_by_ip(ipaddr, "mDns")

    def __init__(self, root):
        self._root = root
        self._zeroconf = None
        self._browser = None

    def start(self):
        self._zeroconf = zeroconf = Zeroconf()
        self._browser = \
            ServiceBrowser(zeroconf, "_http._tcp.local.", self)

    def close(self):
        if self._zeroconf:
            self._zeroconf.close()
            self._zeroconf = None
