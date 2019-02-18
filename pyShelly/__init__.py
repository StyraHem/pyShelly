
# -*- coding: utf-8 -*-

from datetime import timedelta, datetime

import threading
import socket
import struct
import json
import logging

try:
	import http.client as httplib
except:
	import httplib

import sys
if sys.version_info < (3,):
	def ba2c(x): #Convert bytearra to compatible string
		return str(x)
	def b(x):
		return bytearray(x)
	def s(x):
		return str(x)
else:
	def ba2c(x): #Convert bytearra to compatible bytearray
		return x
	def b(x):
		return x
	def s(x):
		return str(x, 'cp1252')

name = "pyShelly"

COAP_IP = "224.0.1.187"
COAP_PORT = 5683

__version__ = "0.0.8"
VERSION = __version__

SHELLY_TYPES = {
	'SHSW-1' 	 : { 'name': "Shelly 1" },
	'SHSW-21' 	 : { 'name': "Shelly 2" },
	'SHPLG-1' 	 : { 'name': "Shelly Plug" },
	'SHRGBWW-01' : { 'name': "Shelly RGBWW" },
	'SHSW-44'	 : { 'name': "Shelly 4 Pro" },
	'SHBLB-1'	 : { 'name': "Shelly Bulb" },
	'SHHT-1'	 : { 'name': "Shelly H&T" },
}

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

	def _httpGet(self, url):
		conn = httplib.HTTPConnection(self.ipaddr)
		conn.request("GET", url)
		resp = conn.getresponse()
		body = resp.read()
		respJson = json.loads(body)
		conn.close()
		return respJson

	def _setup(self):		
		if self.type == 'SHBLB-1':
			self._addDevice( pyShellyRGB(self) )
		elif self.type == 'SHSW-21':
			settings = self._httpGet("/settings")
			if settings['mode'] == 'roller':
				self._addDevice( pyShellyRoller(self) )
			else:
				self._addDevice( pyShellyRelay(self,1,0,2) )
				self._addDevice( pyShellyRelay(self,2,1,2) )
		elif self.type == 'SHSW-1':
			self._addDevice( pyShellyRelay(self,0 , 0) )
		elif self.type == 'SHSW-44':
			for ch in range(4):			
				self._addDevice( pyShellyRelay(self, ch+1, ch*2+1, ch*2) )				
		elif self.type == 'SHRGBWW-01':
			self._addDevice( pyShellyRGB(self) )
		elif self.type == 'SHPLG-1':
			self._addDevice( pyShellyRelay(self, 0, 1, 0) )
		elif self.type == 'SHHT-1':
			self._addDevice( pyShellySensor(self) )
			
	def _addDevice(self, dev):
		self.devices.append( dev )
		self.parent._addDevice( dev, self.code )
		return dev

class pyShellyDevice(object):
	def __init__(self, block):
		self.block = block
		self.id = block.id
		self.type = block.type
		self.ipaddr = block.ipaddr
		self.cb_updated = None
		self.lastUpdated = None
		self.isSensor = False
		self.mode = None
		self._unavailableAfterSec = 60

	def typeName(self):
		try:
			name = SHELLY_TYPES[self.type]['name']
		except:
			name = self.type
		if self.mode is not None:
			name = name + " (" + self.mode + ")"
		return name

	def _sendCommand(self, url):
		conn = httplib.HTTPConnection(self.block.ipaddr)
		conn.request("GET", url)
		resp = conn.getresponse()
		conn.close()
		
	def available(self):
		if self.lastUpdated is None: 
			return False
		diff = datetime.now()-self.lastUpdated
		return diff.total_seconds() < self._unavailableAfterSec

	def _update(self, newState=None, newStateValue=None, newValues=None):
		self.lastUpdated = datetime.now()
		needUpdate = False
		if newState is not None:
			if self.state != newState:
				self.state = newState		
				needUpdate = True
		if newStateValue is not None:
			if self.stateValue != newStateValue:
				self.stateValue = newStateValue		
				needUpdate = True
		if newValues is not None:
			self.sensorValues = newValues	
			needUpdate = True
		if needUpdate:
			self._raiseUpdated()
			
	def _raiseUpdated(self):		
		if self.cb_updated is not None:
			self.cb_updated()

class pyShellyRelay(pyShellyDevice):
	def __init__(self, block, channel, pos, power=None):
		super(pyShellyRelay, self).__init__(block)
		self.id = block.id;
		if channel>0: 
			self.id = self.id + '-' + str(channel)
			self._channel = channel-1	
		else:
			self._channel = 0		
		self._pos = pos
		self._power = power
		self.state = None
		self.devType = "RELAY"
		self.isSensor = power is not None
						
	def update(self,data):
		newState = data['G'][self._pos][2]==1
		newValues = None
		if self._power is not None:
			watt = data['G'][self._power][2]
			newValues = { 'watt' : watt }
		self._update(newState, None, newValues)

	def turnOn(self):
		self._sendCommand( "/relay/" + str(self._channel) + "?turn=on" )
		
	def turnOff(self):
		self._sendCommand( "/relay/" + str(self._channel) + "?turn=off" )
		
#class pyShellyPowerMeter(pyShellyDevice):
#	def __init__(self, block, chan, pos):
#		super(pyShellyPowerMeter, self).__init__(block)
#		self.id = block.id + "-" + str(chan)
#		self._pos = pos
#		self.sensorValues = None
#		self.devType = "POWER_METER"
#		
#	def update(self,data):
#		watt = data['G'][self._pos][2]
#		self._update(None, None, { 'watt' : watt })

class pyShellyRoller(pyShellyDevice):
	def __init__(self, block):
		super(pyShellyRoller, self).__init__(block)
		self.id = block.id
		self.devType = "ROLLER"
		self.state = None
		self.position = None	
		self.isSensor = True
		self.mode = "Roller"
		self.upsideDown = True
		
	def update(self,data):
		states = data['G']
		settings = self.block._httpGet("/roller/0")
		self.position = settings['current_pos']
		watt = data['G'][2][2]
		#if not self.invert:
		state = self.position!=0
		#else:
		#	state = self.position==0
		self._update(state, None, { 'watt' : watt } )

	def up(self):
		self._sendCommand( "/roller/0?go=" + ( "open" if not self.upsideDown else "close" ) )

	def down(self):
		self._sendCommand( "/roller/0?go="  + ( "close" if not self.upsideDown else "open" ) )

	def stop(self):
		self._sendCommand( "/roller/0?go=stop" )
		
	#def turnOn(self):
	#	self.up()

	#def turnOff(self):
	#	self.down()
	
		
class pyShellyRGB(pyShellyDevice):
	def __init__(self, block):
		super(pyShellyRGB, self).__init__(block)		
		self.id = block.id
		self.state = None
		self.stateValue = None
		self.devType = "RGB"
		
		self.isModeWhite = None
		self.gain = None
		self.brightness = None

	def update(self,data):
		newState = data['G'][4][2]==1
		settings = self.block._httpGet("/light/0")
		self.gain = int(settings['gain'])
		self.brightness = int(settings['brightness'])
		self.isModeWhite = settings['mode']=='white'
		
		value = self.brightness if self.isModeWhite else self.gain
		self._update(newState, value)

	def _sendData(self, newState, newStateValue=0):
		if not newState or newStateValue==0:
			self._sendCommand( "/light/0?turn=off" )
		elif self.isModeWhite:
			self._sendCommand( "/light/0?mode=white&turn=on&brightness=" + str(newStateValue) )
		else:
			self._sendCommand( "/light/0?mode=color&turn=on&gain=" + str(newStateValue) )

	def turnOn(self):
		self._sendData(True, 100)
		
	def turnOff(self):
		self._sendData(False)
	
	def dim(self, value):		
		self._sendData(True, value)
		
class pyShellySensor(pyShellyDevice):
	def __init__(self, block):
		super(pyShellySensor, self).__init__(block)		
		self.id = block.id
		self.state = None
		self.stateValue = None
		self.devType = "SENSOR"
		self._unavailableAfterSec = 3600*3	#TODO, read from settings

	def update(self,data):
		temp = float(data['G'][0][2])
		humidity = float(data['G'][1][2])
		battery = int(data['G'][2][2])
		self._update(None, None, { 'temperature' : temp, 'humidity' : humidity, 'battery' : battery })

class pyShelly():
	def __init__(self):
		logging.info("Init pyShelly " + VERSION)
		
		self.stopped = threading.Event()
		self.blocks = {}
		self.devices = []
		self.cb_deviceAdded = None
		self.igmpFixEnabled = False	#Used if igmp packages not sent correctly
		
	def open(self):	
		self.initSocket()
		self._udp_thread = threading.Thread(target=self._udp_reader)
		self._udp_thread.start()		
		
	def version(self):
		return VERSION
		
	def initSocket(self):
		s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
		s.bind(('', COAP_PORT))
		
		mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP), socket.INADDR_ANY)
		s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
				
		s.settimeout(15)
		
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
		msg = bytes(b'\x50\x01\x00\x0A\xb3cit\x01d\xFF')
		#msg = bytes([0x50, 0x01, 0x00, 0x0A, 0xb3, b'c', b'i', b't', 0x01, b'd', 0xFF])
		#msg = chr(0x50) + chr(1) + chr(0) + chr(10) + chr(0xb3) + "cit" + chr(0x01) + 'd' + chr(0xFF)
		self._socket.sendto(msg, (COAP_IP, COAP_PORT))

	def _addDevice(self, dev, code):
		#logging.info('Add device')
		self.devices.append (dev )
		if self.cb_deviceAdded is not None:
			self.cb_deviceAdded(dev, code)

	def _udp_reader(self):			
		
		nextIGMPfix = datetime.now() + timedelta(minutes=1)
		
		while not self.stopped.isSet():
			
			#This fix is needed if not sending IGMP reports correct
			if self.igmpFixEnabled and datetime.now()>nextIGMPfix:
				mreq = struct.pack("=4sl", socket.inet_aton(COAP_IP), socket.INADDR_ANY)
				self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
				self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
				nextIGMPfix = datetime.now() + timedelta(minutes=1)

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
 
					byte = data[pos]

				payload = s(data[pos+1:])

				#logging.info('Type %s, Id %s, Payload %s', type, id, payload)						
				
				if id not in self.blocks:
					self.blocks[id] = pyShellyBlock(self, id, type, addr[0], code)

				if code==30:
					self.blocks[id].update(json.loads(payload))
