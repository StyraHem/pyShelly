from datetime import datetime

from .const import (
    LOGGER,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_POS,
    ATTR_CHANNEL,
    REGEX_VER
)

class Base(object):

    def __init__(self):
        self.info_values = {}
        self.info_values_updated = {}
        self._info_value_cfg = None
        self.info_values_status_value = {}
        self.info_values_coap = {}
        self._state_cfg = None
        self.state_status = None
        self.state_coap = None
        self._channel = 0

    def _fmt_info_value(self, value, cfg, prefix):
        fmt_list = cfg.get(ATTR_FMT, None)
        if type(fmt_list) is dict:
            fmt_list = fmt_list.get(prefix)
        if fmt_list:
            if not type(fmt_list) is list:
                fmt_list = [fmt_list]
            for fmt in fmt_list:
                if callable(fmt):
                    value = fmt(value)
                    continue
                params = fmt.split(':')
                cmd = params[0]
                if cmd == 'bool':
                    value = value > 0
                elif cmd == "round":
                    if len(params)>1:
                        value = round(value, int(params[1]))
                    else:
                        value = round(value)
                elif cmd == "float":
                    value = float(value)
                elif cmd[0] == '/':
                    div = int(fmt[1:])
                    value = value / div
                elif cmd == "ver":
                    value = self.parent._firmware_mgr.format(value)
        return value

    def _get_status_value(self, status, cfg):
        value = status
        path = cfg.get(ATTR_PATH)
        if not path:
            return None
        for key in path.split('/'):
            if value is not None:
                if key == '$':
                    ch = cfg.get(ATTR_CHANNEL, self._channel)
                    #idx = min(self._channel, len(value)-1) #Meters Shelly 2,5
                    value = value[ch]
                else:
                    value = value.get(key, None)
        return value

    def _update_state(self, status, cfg):
        value = self._get_status_value(status, cfg)
        if value is not None:
            value = self._fmt_info_value(value, cfg, "STATUS")
            self.state = value
            self.state_status = value
            if self.lazy_load:
                self.block.parent.callback_add_device(self)

    def _update_info_value(self, name, status, cfg):
        value = self._get_status_value(status, cfg)
        if value is not None:
            value = self._fmt_info_value(value, cfg, "STATUS")
            self.info_values[name] = value
            self.info_values_updated[name] = datetime.now()
            self.info_values_status_value[name] = value

    def _get_coap_value(self, cfg, payload):
        if ATTR_POS in cfg:
            pos_list = cfg[ATTR_POS]
            if not type(pos_list) is list:
                pos_list = [pos_list]
            for _pos in pos_list:
                ch = cfg.get(ATTR_CHANNEL, self._channel)
                if _pos < 1000:
                    pos = _pos + 10 * ch
                else:
                    pos = _pos + 100 * ch
                if pos in payload:
                    value = payload.get(pos)
                    value = self._fmt_info_value(value, cfg, "COAP")
                    return value
        return None

    def _update_info_values_coap(self, payload):
        if self._state_cfg:
            self.state = self._get_coap_value(self._state_cfg, payload)
            self.state_coap = self.state
            need_update = True
        if self._info_value_cfg:
            need_update = False
            for name, cfg in self._info_value_cfg.items():
                value = self._get_coap_value(cfg, payload)
                if value is not None:
                    self.info_values_updated[name] = datetime.now()
                    self.info_values_coap[name] = value
                    if self.info_values.get(name)!=value:
                        self.info_values[name] = value
                        need_update = True
            if need_update:
                self.raise_updated()

    #Todo: remove
    def coap_get(self, payload, pos_list, default=None):
        if pos_list is None:
            return default
        if not type(pos_list) is list:
            pos_list = [pos_list]
        for _pos in pos_list:
            ch = self._channel or 0
            if _pos < 1000:
                pos = _pos + 10 * ch
            else:
                pos = _pos + 100 * ch
            if pos in payload:
                return payload[pos]
        return default

