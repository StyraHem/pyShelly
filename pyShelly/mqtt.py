import socket
import threading
import json

from .const import (
    LOGGER, SHELLY_TYPES
)

class MQTT_connection:
    def __init__(self, mqtt, connection, client_address):
        self._mqtt = mqtt
        self._connection = connection
        #connection.settimeout(5)
        self._client_address = client_address
        self._thread = threading.Thread(target=self._loop)
        self._thread.name = "MQTT connection"
        self._thread.daemon = True
        self._thread.start()

    def _loop(self):
        try:
            # Receive the data in small chunks and retransmit it
            while not self._mqtt._root.stopped.isSet():
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
                    LOGGER.debug(f"type=%d, flags=%d, length=%d" %
                                        (pkg_type, flags, length))

                    data = self._connection.recv(length) if length else None
                    if pkg_type==1:
                        msg = b'\x20\x04\x20\x00\x00\0x00'
                        self._connection.send(msg)
                    if pkg_type==3:
                        topic_len = (data[0]<<8) + data[1]
                        topic = data[2:2+topic_len].decode('ASCII') 
                        payload = data[2+topic_len:]
                        if topic=='shellies/announce':
                            payload = json.loads(payload)
                            ip_addr = payload['ip']
                            shelly_id = payload['id']
                            shelly_type, device_id = shelly_id.rsplit('-',1)
                            device_type = self._mqtt._mqtt_types.get(shelly_type)
                            if device_type:
                                self._mqtt._root.update_block(device_id, \
                                    device_type, ip_addr, 'MQTT-discovery', None)
                        else:
                            topics = topic.split('/')
                            shelly_id = topics[1]
                            shelly_type, device_id = shelly_id.rsplit('-',1)
                            device_type = self._mqtt._mqtt_types.get(shelly_type)
                            self._mqtt._root.update_block(device_id, \
                                    device_type, None, 'MQTT-data', None, True)
                    if pkg_type==12:
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
                self._mqtt._connections.remove(self)
            except:
                pass

class MQTT():

    def __init__(self, root):
        self._root = root
        self._thread = threading.Thread(target=self._loop)
        self._thread.name = "MQTT"
        self._thread.daemon = True
        self._socket = None
        self._connections = []
        self._mqtt_types = {}
        for key, item in SHELLY_TYPES.items():
            if 'mqtt' in item:
                self._mqtt_types[item['mqtt']]=key

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
            except Exception as ex:
                LOGGER.exception("Error connect MQTT")

    def close(self):
        if self._socket:
            self._socket.close()
