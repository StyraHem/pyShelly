# -*- coding: utf-8 -*-

import threading
import socket
import struct
import json
import logging
import httplib

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

class pyShellyBlock():
    def __init__(self, parent, id, type, ipaddr):
        self.id = id
        self.type = type
        self.parent = parent
        self.ipaddr = ipaddr
        self.devices = []
        self._setup()        
        print "Added " + id, type, ipaddr

    def update(self, data):
        for dev in self.devices:
            dev.update(data)

    def _setup(self):
        conn = httplib.HTTPConnection(self.ipaddr)
        conn.request("GET", "/settings")
        resp = conn.getresponse()
        settings = json.loads(resp.read())
        conn.close()

        if self.type == 'SHBLB-1':
            self._addDevice( pyShellyRGB(self) )
        elif self.type == 'SHSW-21':
            if settings['mode'] == 'roller':
                self._addDevice( pyShellyRoller(self) )
            else:
                self._addDevice( pyShellyRelay(self,0) )
                self._addDevice( pyShellyRelay(self,1) )
        elif self.type == 'SHSW-1':
            self._addDevice( pyShellyRelay(self,0) )
        elif self.type == 'SHRGBWW-01':
            self._addDevice( pyShellyRGB(self) )
            
    def _addDevice(self, dev):
        self.devices.append( dev )
        self.parent._addDevice( dev )


class pyShellyDevice(object):
    def __init__(self, block):
        self.block = block
        self.id = block.id
        self.type = block.type
        self.ipaddr = block.ipaddr
        self.cb_updated = None

    def _sendCommand(self, url):
        conn = httplib.HTTPConnection(self.block.ipaddr)
        conn.request("GET", url)
        resp = conn.getresponse()
        conn.close()
        
    def _raiseUpdated(self):
        if self.cb_updated is not None:
            self.cb_updated()

class pyShellyRelay(pyShellyDevice):
    def __init__(self, block, channel):
        super(pyShellyRelay, self).__init__(block)
        self.id = block.id + "-RELAY-" + str(channel)
        self._channel = channel
        self.state = None
                        
    def update(self,data):
        newState = data['G'][self._channel][2]==1
        if self.state != newState:
            self.state = newState
            self._raiseUpdated()

    def turnOn(self):
        self._sendCommand( "/relay/" + str(self._channel) + "?turn=on" )
        
    def turnOff(self):
        self._sendCommand( "/relay/" + str(self._channel) + "?turn=off" )
        

class pyShellyPowerMeter(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyPowerMeter, self).__init__(block)
        self.id = block.id + "-POWERMETER"
        self.value = 0
        
    def update(self,data):
        watt = data['G'][2][2]
        self.value=watt

class pyShellyRoller(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyRoller, self).__init__(block)
        self.id = block.id + "-ROLLER"

    def update(self,data):
        states = data['G']
        #self.setState(Device.TURNON if states[self.__channel][2]==1 else Device.TURNOFF)

    def up(self):
        self._sendCommand( "/roller/0?go=open" )

    def down(self):
        self._sendCommand( "/roller/0?go=close" )

    def stop(self):
        self._sendCommand( "/roller/0?go=stop" )
        
class pyShellyRGB(pyShellyDevice):
    def __init__(self, block):
        super(pyShellyRGB, self).__init__(block)        
        self.id = block.id + "-RGB"
        self.state = None

    def update(self,data):
        newState = data['G'][4][2]==1
        if newState != self.state:
            self.state = newState
            self._raiseUpdated()

    def turnOn(self):
        self._sendCommand( "/light/0?turn=on" )
        
    def turnOff(self):
        self._sendCommand( "/light/0?turn=off" )


class pyShelly():
    def __init__(self):
        self.stopped = threading.Event()
        self.blocks = {}   
        self.devices = []
        self.cb_deviceAdded = None

        self._socket = s = socket.socket(socket.AF_INET,
                   socket.SOCK_DGRAM, socket.IPPROTO_UDP)

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

    def _addDevice(self, dev):
        self.devices.append (dev )
        if self.cb_deviceAdded is not None:
            self.cb_deviceAdded(dev)

    def _udp_reader(self):
        while not self.stopped.isSet():
            self._socket.settimeout(1)
            
            try:
                data, addr = self._socket.recvfrom(10240)
            except socket.timeout:  # pragma: no cover
                continue

            byte = ord(data[0])
            ver = byte >> 6
            type = (byte >> 4) & 0x3
            tokenlen = byte & 0xF
            
            code = ord(data[1])
            msgid = 256 * ord(data[2]) + ord(data[3])
            
            #print "Code:", code , ", MsgId:" , msgid, " Addr:" , addr[0]

            pos = 4
            
            if code == 30 or code == 69 :

                byte = ord(data[pos])
                totDelta = 0

                type = "";
                id = "";

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

                    if totDelta==3332:
                        type, id, _ = value.split('#',2)

                    byte = ord(data[pos])

                payload = data[pos+1:]

                logging.info('Type %s, Id %s, Payload %s', type, id, payload)
                
                if id not in self.blocks:
                    self.blocks[id] = pyShellyBlock(self, id, type, addr[0])

                if code==30:
                    self.blocks[id].update(json.loads(payload))
