from .compat import s

from .const import (
    LOGGER, SHELLY_TYPES
)

class MQTT():

    def __init__(self, root, name):
        self._root = root
        self.src = name
        self._mqtt_types = {}
        for key, item in SHELLY_TYPES.items():
            if 'mqtt' in item:
                self._mqtt_types[item['mqtt']]=key

    def receive_msg(self, topic, data):
        try:
            if not topic.startswith("shellies/shelly"):
                return

            _, name, cmd = topic.split('/', 2)
            if name == 'announce':
                return
            _type, device_id = name.rsplit('-', 1)
            device_type = self._mqtt_types.get(_type)
            payload = {
                'type': 'mqtt',
                'name': name,
                'topic': cmd,
                'data': data,
                'src':  self.src
            }
            self._root.update_block(device_id, \
                device_type, None, 'MQTT', payload, mqtt=name)
        except:
            
            LOGGER.exception("Error parsing MQTT message, " + self.src + ", " + topic)