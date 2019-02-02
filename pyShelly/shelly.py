# -*- coding: utf-8 -*-

import threading
import socket
import struct
import json
import logging
#import httplib

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

class ShellyDevice():
    def __init__(self, id, type, ipaddr):
        self.id = id
        self.type = type
        self.ipaddr = ipaddr
        print id, type, ipaddr

    def update(self, data):
        print data
        
class Shelly():
    def __init__(self):
        self.stopped = threading.Event()
        self.devices = {}        

        self._socket = s = socket.socket(socket.AF_INET, # Internet
                   socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', COAP_PORT))
        mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self._udp_thread = threading.Thread(target=self._udp_reader)
        self._udp_thread.start()

    def close(self):
        self.stopped.set()
        if self._udp_thread is not None:
            self._udp_thread.join()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self._socket.close()
        
    def discover(self):
        msg = chr(0x50) + chr(1) + chr(0) + chr(10) + chr(0xb3) + "cit" + chr(0x01) + 'd' + chr(0xFF)      
        self._socket.sendto(msg, (COAP_IP, COAP_PORT))

    def _udp_reader(self):
        while not self.stopped.isSet():
            self._socket.settimeout(1)

            print '.'
            
            try:
                data, addr = self._socket.recvfrom(10240)
            except socket.timeout:  # pragma: no cover
                continue

            print 'UDP'
            
            byte = ord(data[0])
            ver = byte >> 6
            type = (byte >> 4) & 0x3
            tokenlen = byte & 0xF
            
            #print "DATA:" + data

            code = ord(data[1])
            msgid = 256 * ord(data[2]) + ord(data[3])
            
            print "Code:", code , ", MsgId:" , msgid, " Addr:" , addr[0]

            pos = 4
            
            if code == 30 or code == 69 :

                byte = ord(data[pos])
                totDelta = 0

                devType = "";
                devId = "";

                while byte<>0xFF:
                    delta = byte >> 4
                    len = byte & 0x0F

                    if delta==13:
                        pos=pos+1
                        delta = ord(data[pos])+13
                    elif delta==14:
                        pos=pos+2
                        delta = ord(data[pos-1])*256 + ord(data[pos]) + 269

                    totDelta = totDelta + delta

                    if len==13:
                        pos=pos+1
                        len = ord(data[pos])+13
                    elif len==14:
                        pos=pos+2
                        len = ord(data[pos-1])*256 + ord(data[pos]) + 269

                    value = data[pos+1:pos+1+len]
                    pos = pos + len +1;

                    #print totDelta, len, value

                    if totDelta==3332:
                        devType, devId, rest = value.split('#',2)

                    byte = ord(data[pos])

                payload = data[pos+1:]

                logging.info('Type %s, Id %s, Payload %s', devType, devId, payload)
                
                if devId not in self.devices:
                    self.devices[devId] = ShellyDevice(devId, devType, addr[0])
                    
                self.devices[devId].update(json.loads(payload))
    

s = Shelly()
s.discover()
