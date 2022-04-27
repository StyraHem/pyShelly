import codecs
import socket
import threading
import json
from .compat import b
from .mqtt import MQTT
from .const import (
    LOGGER, SHELLY_TYPES
)
from .utils import (exception_log, warning_log)

class MQTT_connection:
    def __init__(self, mqtt, connection, client_address):
        self._mqtt_server = mqtt
       
        self._connection = connection
        #connection.settimeout(5)
        self._id = None
        self._client_address = client_address
        self._thread = threading.Thread(target=self._loop)
        self._thread.name = "MQTT connection"
        self._thread.daemon = True
        self._thread.start()

    def _loop(self):
        try:
            while not self._mqtt_server._root.stopped.isSet():
                try:
                    head = b(self._connection.recv(1))
                    if not head:
                        break
                    pkg_type=head[0]>>4
                    flags=head[0]&0xF
                    qos = (flags >> 1) & 0x3
                    length = 0
                    for s in range(0,4):
                        ldata = b(self._connection.recv(1))[0]
                        length += (ldata & 0x7F) << (s * 7)
                        if not ldata & 128:
                            break
                    LOGGER.debug("type=%d, flags=%d, length=%d", pkg_type, flags, length)
                    data = b(self._connection.recv(length, socket.MSG_WAITALL)) if length else []
                    if (len(data)!=length):
                        warning_log("Receiving wrong size of MQTT message", length, len(data))
                        print(data.decode('ASCII'))
                        break
                    
                    if pkg_type==1: #connected
                        if data[0]!=0 or data[1]!=4 or data[2:6]!=b'MQTT':
                            break
                        client_len = (data[10] << 8) + data[11]
                        id = data[12:12+client_len].decode()
                        self._id = id
                        msg = b'\x20\x02\x20\x00'
                        self._connection.send(msg)
                        msg = self._mqtt_server.create_msg(self._id, 'command', 'announce')
                        self._connection.send(msg)
                    elif pkg_type==3:
                        pos = 2
                        topic_len = (data[0]<<8) + data[1]
                        topic = data[pos:pos+topic_len].decode('ASCII') 
                        pos += topic_len
                        if qos>0: 
                            pos+=2
                        payload = data[pos:].decode('ASCII')
                        self._mqtt_server.receive_msg(topic, payload)
                        # if topic=='shellies/announce':
                        #     payload = json.loads(payload)
                        #     ip_addr = payload['ip']
                        #     shelly_id = payload['id']
                        #     shelly_type, device_id = shelly_id.rsplit('-',1)
                        #     device_type = self._mqtt_server._mqtt_types.get(shelly_type)
                        #     if device_type:
                        #         self._mqtt_server._root.update_block(device_id, \
                        #             device_type, ip_addr, 'MQTT-discovery', None)
                        # else:
                        #     topics = topic.split('/')
                        #     shelly_id = topics[1]
                        #     shelly_type, device_id = shelly_id.rsplit('-',1)
                        #     device_type = self._mqtt_server._mqtt_types.get(shelly_type)
                        #     self._mqtt_server._root.update_block(device_id, \
                        #             device_type, None, 'MQTT-data', None, True)   
                    elif pkg_type==8:  #Subscribe  
                        msg = b'\x90\x03'
                        #msg += ((data[0]<<8) + data[1]).to_bytes(2, 'big')
                        n = (data[0]<<8) + data[1]
                        h = '%x' % n
                        s = ('0'*(len(h) % 2) + h).zfill(length*2)
                        s = codecs.decode(s, 'hex')
                        msg += s
                        msg += b'\x01'
                        self._connection.send(msg)                 
                    elif pkg_type==12: #Ping
                        msg = b'\xD0\x00'
                        self._connection.send(msg)
                    else:
                        print("Unknown MQTT Message ", pkg_type)
                except socket.timeout:
                    pass
                except Exception as ex:
                    exception_log(ex, "Error receiving MQTT message")
                    break
        finally:
            #Clean up
            try:
                self._connection.close()
            except:
                pass
            try:
                self._mqtt_server._connections.remove(self)
            except:
                pass
    
    def send(self, data):
        try:            
            self._connection.send(data)
        except:
            LOGGER.exception("Error sending MQTT")


class MQTT_server(MQTT):

    def __init__(self, root):
        super(MQTT_server, self).__init__(root, "Server")
        self._thread = threading.Thread(target=self._loop)
        self._thread.name = "S4H-MQTT"
        self._thread.daemon = True
        self._socket = None
        self._connections = []

    def start(self):
        if self._root.mqtt_port > 0:
            self._init_socket()
            self._thread.start()

    def _init_socket(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self._root.bind_ip, self._root.mqtt_port))
        sock.listen(1)
        sock.settimeout(1)
        self._socket = sock

    def _loop(self):

        while not self._root.stopped.isSet():
            try:
                # Wait for a connection
                connection, client_address = self._socket.accept()
                #print("MQTT Connection", client_address)
                conn = MQTT_connection(self, connection, client_address)
                self._connections.append(conn)
            except socket.timeout:
                pass
            except:
                if not self._root.stopped.isSet():
                    LOGGER.exception("Error connect MQTT")

    def close(self):
        if self._socket:
            self._socket.close()

    def _add_len(self, data):
        length = len(data)
        data.insert(0, length & 0x7F)        
        while length > 0x7f:
            length >>= 7
            data.insert(0, (length & 0x7F) | 0x80)

    def create_msg(self, name, topic, payload):
        #t = "shellies/" + name + "/" + topic
        data = bytearray(topic, 'cp1252')
        data.insert(0, len(topic) >> 8)
        data.insert(1, len(topic) & 0xFF)
        data.extend(bytearray(payload, 'cp1252'))
        self._add_len(data)
        data.insert(0, 0x30)
        return data

    def send(self, block, topic, payload):
        data = self.create_msg(block.mqtt_name, topic, payload)
        for conn in self._connections:
            if block.mqtt_name == conn._id:
                conn.send(data)


