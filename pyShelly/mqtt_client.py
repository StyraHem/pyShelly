try:
    import paho.mqtt.client as mqtt
except:
    pass
from .compat import s
from .mqtt import MQTT
from .const import (
    LOGGER, SHELLY_TYPES
)

class MQTT_client(MQTT):

    def __init__(self, root):
        super(MQTT_client, self).__init__(root, "Client")
        self._client = None                

    def start(self):
        if self._root.mqtt_server_host and self._root.mqtt_server_port:
            self._client = mqtt.Client()
            self._client.on_connect = self.on_connect
            self._client.on_message = self.on_message

            if self._root.mqtt_server_username:
                self._client.username_pw_set(self._root.mqtt_server_username, self._root.mqtt_server_password)

            self._client.connect_async(self._root.mqtt_server_host, self._root.mqtt_server_port, 60)
            self._client.loop_start()

    def close(self):
        if self._client:
            self._client.loop_stop()
            self._client = None

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe("shellies/#")
        client.subscribe("+/events/rpc")
        client.subscribe("+/status/+")
        client.subscribe("shelly4hass/#")
        client.publish("shellies/command", "announce")
            
    def on_message(self, client, userdata, msg):
        self.receive_msg(msg.topic, s(msg.payload))

    def send(self, block, topic, payload):
        #t = "shellies/" + block.mqtt_name + "/" + topic
        self._client.publish(topic, payload)

