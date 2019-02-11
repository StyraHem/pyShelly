# -*- coding: utf-8 -*-

from datetime import timedelta, datetime

import threading
import socket
import struct
import json
import logging
import http.client	#import httplib

import sys
if sys.version_info < (3,):
    def b(x):
        return bytearray(x)
    def s(x):
        return str(x)
else:
    def b(x):
        return x
    def s(x):
        return str(x, 'cp1252')

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

class pyShellyBlock():
	def __init__(self, parent, id, type, ipaddr, code):		
		self.id = id
		self.type = type
		self.parent = parent
		self.ipaddr = ipaddr
		self.devices = []
		self.code = code	#DEBUG
		self._setup()

	def update(self, data):
		#logging.info("BlockUpdate!! " + str(data))
		for dev in self.devices:
			dev.update(data)

	def _setup(self):
		conn = http.client.HTTPConnection(self.ipaddr)
		conn.request("GET", "/settings")
		resp = conn.getresponse()
		settings = json.loads(resp.read())
		conn.close()

		if self.type == 'SHBLB-1':
			self._addDevice( pyShellyRGB(self) )
		elif self.type == 'SHSW-21':
			#self._addDevice( pyShellyPowerMeter(self, 2) )
			if settings['mode'] == 'roller':
				self._addDevice( pyShellyRoller(self) )
			else:
				self._addDevice( pyShellyRelay(self,0,0) )
				self._addDevice( pyShellyRelay(self,1,1) )
		elif self.type == 'SHSW-1':
			self._addDevice( pyShellyRelay(self,0,0) )
		elif self.type == 'SHRGBWW-01':
			self._addDevice( pyShellyRGB(self) )
		elif self.type == 'SHPLG-1':
			#self._addDevice( pyShellyPowerMeter(self, 0) )
			self._addDevice( pyShellyRelay(self, 0, 1) )
			
	def _addDevice(self, dev):
		self.devices.append( dev )
		self.parent._addDevice( dev, self.code )

class pyShellyDevice(object):
	def __init__(self, block):
		self.block = block
		self.id = block.id
		self.type = block.type
		self.ipaddr = block.ipaddr
		self.cb_updated = None
		self.lastUpdated = None

	def _sendCommand(self, url):
		conn = http.client.HTTPConnection(self.block.ipaddr)
		conn.request("GET", url)
		print ("Sending to " + url)
		resp = conn.getresponse()
		conn.close()
		
	def available(self):
		if self.lastUpdated is None: 
			return False
		diff = datetime.now()-self.lastUpdated
		return diff.total_seconds() < 60

	def _updateState(self, newState):
		self.lastUpdated = datetime.now()
		if self.state != newState:
			self.state = newState
			self._raiseUpdated()

	def _raiseUpdated(self):		
		if self.cb_updated is not None:
			self.cb_updated()

class pyShellyRelay(pyShellyDevice):
	def __init__(self, block, channel, pos):
		super(pyShellyRelay, self).__init__(block)
		self.id = block.id + "-RELAY-" + str(channel)
		self._channel = channel
		self._pos = pos
		self.state = None
		self.devType = "RELAY"
						
	def update(self,data):
		newState = data['G'][self._pos][2]==1
		self._updateState(newState)

	def turnOn(self):
		self._sendCommand( "/relay/" + str(self._channel) + "?turn=on" )
		
	def turnOff(self):
		self._sendCommand( "/relay/" + str(self._channel) + "?turn=off" )
		
class pyShellyPowerMeter(pyShellyDevice):
	def __init__(self, block, pos):
		super(pyShellyPowerMeter, self).__init__(block)
		self.id = block.id + "-POWERMETER"
		self.pos = pos
		self.value = 0
		self.devType = "POWER_METER"
		
	def update(self,data):
		watt = data['G'][self.pos][2]
		self.value=watt

class pyShellyRoller(pyShellyDevice):
	def __init__(self, block):
		super(pyShellyRoller, self).__init__(block)
		self.id = block.id + "-ROLLER"
		self.devType = "ROLLER"

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
		self.devType = "RGB"

	def update(self,data):
		newState = data['G'][4][2]==1
		self._updateState(newState)

	def turnOn(self):
		self._sendCommand( "/light/0?turn=on" )
		
	def turnOff(self):
		self._sendCommand( "/light/0?turn=off" )

class pyShelly():
	def __init__(self):
		logging.info('Init pyShelly')
		
		self.stopped = threading.Event()
		self.blocks = {}
		self.devices = []
		self.cb_deviceAdded = None

		self.initSocket()

		self._udp_thread = threading.Thread(target=self._udp_reader)
		self._udp_thread.start()
		
	def initSocket(self):
		s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		
		res = s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		#logging.info("SOL_SOCKET=" + str(res))
		s.bind(('', COAP_PORT))
		
		mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP), socket.INADDR_ANY)
		res = s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
		#logging.info("IP_ADD_MEMBERSHIP=" + str(res))
		
		s.settimeout(10)
		
		self._socket = s
		
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

	def _addDevice(self, dev, code):
		#logging.info('Add device')
		self.devices.append (dev )
		if self.cb_deviceAdded is not None:
			self.cb_deviceAdded(dev, code)

	def _udp_reader(self):
		while not self.stopped.isSet():
			try:
				dataTmp, addr = self._socket.recvfrom(500)
			except socket.timeout:
				continue

			data = bytearray(dataTmp)
			#logging.info("Data:" + str(data))
			
			byte = data[0]
			ver = byte >> 6
			typex = (byte >> 4) & 0x3
			tokenlen = byte & 0xF
			
			code = data[1]
			msgid = 256 * data[2] + data[3]
			
			pos = 4
			
			#logging.info('Got UDP ' + str(code))
			
			if code == 30 or code == 69 :

				byte = data[pos]
				totDelta = 0

				type = "";
				id = "";

				while byte!=0xFF:
					delta = byte >> 4
					len = byte & 0x0F

					if delta==13:
						pos=pos+1
						delta = data[pos]+13
					elif delta==14:
						pos=pos+2
						delta = data[pos-1]*256 + data[pos] + 269

					totDelta = totDelta + delta

					if len==13:
						pos=pos+1
						len = data[pos]+13
					elif len==14:
						pos=pos+2
						len = data[pos-1]*256 + data[pos] + 269
					
					value = data[pos+1:pos+len]
					pos = pos + len +1;								
					
					if totDelta==3332:
						type, id, _ = s(value).split('#',2)
						print(type, id)
 
					byte = data[pos]

				payload = s(data[pos+1:])

				#logging.info('Type %s, Id %s, Payload %s', type, id, payload)						
				
				if id not in self.blocks:
					self.blocks[id] = pyShellyBlock(self, id, type, addr[0], code)

				if code==30:
					self.blocks[id].update(json.loads(payload))
