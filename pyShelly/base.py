from datetime import datetime

from .const import (
    LOGGER,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_POS,
    REGEX_VER
)

class Base(object):

    def __init__(self):
        self.info_values = {}
        self.info_values_updated = {}
        self._info_value_cfg = None
        self.info_values_status_value = {}
        self.info_values_coap = {}

    def _fmt_info_value(self, value, cfg, prefix):
        fmt_list = cfg.get(ATTR_FMT, None)
        if type(fmt_list) is dict:
            fmt_list = fmt_list.get(prefix)
        if fmt_list:
            if not type(fmt_list) is list:
                fmt_list = [fmt_list]
            for fmt in fmt_list:
                print(fmt)
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
                print(value)
        return value

    def _update_info_value(self, name, status, cfg):
        value = status
        path = cfg.get(ATTR_PATH)
        if not path:
            return
        for key in path.split('/'):
            if value is not None:
                if key == '$':
                    idx = min(self._channel, len(value)-1) #Meters Shelly 2,5
                    value = value[idx]
                else:
                    value = value.get(key, None)
        if value is not None:
            value = self._fmt_info_value(value, cfg, "STATUS")
            self.info_values[name] = value
            self.info_values_updated[name] = datetime.now()
            self.info_values_status_value[name] = value

    def _update_info_values_coap(self, payload):
        if self._info_value_cfg:
            need_update = False
            #print("**********************************")
            print(payload)
            for name, cfg in self._info_value_cfg.items():
                #print(name)
                #print(cfg)
                if ATTR_POS in cfg:
                    pos_list = cfg[ATTR_POS]
                    if not type(pos_list) is list:
                        pos_list = [pos_list]
                    for pos in pos_list:
                        if pos in payload:
                            value = payload.get(pos)
                            #print(value)
                            value = self._fmt_info_value(value, cfg, "COAP")
                            #print(value)
                            self.info_values_updated[name] = datetime.now()
                            self.info_values_coap[name] = value
                            if self.info_values.get(name)!=value:
                                self.info_values[name] = value
                                need_update = True
            if need_update:
                self.raise_updated()

    def coap_get(self, data, pos_list):
        if not type(pos_list) is list:
            pos_list = [pos_list]
        for pos in pos_list:
            if pos in data:
                return data[pos]
        return None

