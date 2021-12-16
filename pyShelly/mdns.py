# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except, invalid-name

import re
import ipaddress
from zeroconf import ( ServiceBrowser, Zeroconf )

MATCH_NAME = \
    re.compile("(?P<devtype>shelly.+)-(?P<id>[0-9A-Fa-f]+)._(http|shelly)._tcp.local.")

EXCLUDE = ['shellydw', 'shellyht', 'shellyflood']

class MDns:

    def remove_service(self, _zeroconf, type, name):
        pass

    def get_ip(self, type, name):
        info = self._zeroconf.get_service_info(type, name)
        if info:
            for addr in info.addresses:
                return str(ipaddress.IPv4Address(addr))

    def add_service(self, zeroconf, type, name):
        test = MATCH_NAME.fullmatch(name)
        if test:
            device_type = test.group('devtype')
            device_id = test.group('id')
            if device_type in EXCLUDE:
                return
            info = zeroconf.get_service_info(type, name)
            if info:
                for addr in info.addresses:
                    #ipaddr = str(ipaddress.IPv4Address(addr))
                    self._root.add_device_by_ip("%s|%s" % (type, name) , "mDns")

    def update_service(self, zconf, type, name):
        """ Update a service in the collection. """        
        self.add_service(zconf, type, name)

    def __init__(self, root, zeroconf = None):
        self._root = root
        self._common_zeroconf = zeroconf
        self._zeroconf = None
        self._browser = None
        self._browser2 = None

    def start(self):
        self._zeroconf = zeroconf = self._common_zeroconf or Zeroconf()
        self._browser = \
            ServiceBrowser(zeroconf, ["_http._tcp.local.", "_shelly._tcp.local."], self)
        #self._browser2 = \
        #    ServiceBrowser(zeroconf, "_shelly._tcp.local.", self)
        
    def close(self):
        if self._zeroconf:
            if not self._common_zeroconf:
                self._zeroconf.close()
            self._zeroconf = None
