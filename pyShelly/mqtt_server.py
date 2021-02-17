import socket
import threading
import json
from .mqtt import MQTT
from .const import (
    LOGGER, SHELLY_TYPES
)

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
                    head = self._connection.recv(1)
                    if not head:
                        break
                    pkg_type=head[0]>>4
                    flags=head[0]&0xF
                    length = 0
                    for s in range(0,4):
                        ldata = self._connection.recv(1)[0]
                        length += (ldata & 0x7F) << (s * 7)
                        if not ldata & 128:
                            break
                    LOGGER.debug("type=%d, flags=%d, length=%d", pkg_type, flags, length)
                    data = self._connection.recv(length, socket.MSG_WAITALL) if length else []

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
                    if pkg_type==3:
                        topic_len = (data[0]<<8) + data[1]
                        topic = data[2:2+topic_len].decode('ASCII') 
                        payload = data[2+topic_len:].decode('ASCII')                         
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
                    if pkg_type==12: #Ping
                        msg = b'\xD0\x00'
                        self._connection.send(msg)
                except socket.timeout:
                    pass
                except Exception as ex:
                    LOGGER.exception("Error receiving MQTT message")
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
        self._thread.name = "MQTT"
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
        self._socket = sock

    def _loop(self):

        while not self._root.stopped.isSet():
            try:
                # Wait for a connection
                connection, client_address = self._socket.accept()
                conn = MQTT_connection(self, connection, client_address)
                self._connections.append(conn)
            except:
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
        t = "shellies/" + name + "/" + topic
        data = bytearray(t, 'cp1252')
        data.insert(0, len(t) >> 8)
        data.insert(1, len(t) & 0xFF)
        data.extend(bytearray(payload, 'cp1252'))
        self._add_len(data)
        data.insert(0, 0x30)
        return data

    def send(self, name, topic, payload):
        data = self.create_msg(name, topic, payload)
        for conn in self._connections:
            if name == conn._id:
                conn.send(data)


