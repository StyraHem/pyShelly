import traceback

from datetime import datetime

from .const import (
    BLOCK_INFO_VALUES,
    LOGGER,
    ATTR_PATH,
    ATTR_FMT,
    ATTR_POS,
    ATTR_CHANNEL,
    REGEX_VER,
    SRC_COAP,
    SRC_STATUS
)
class Base(object):

    def __init__(self):
        self.info_values = {}
        self.info_values_updated = {}
        self._info_value_cfg = None
        self.info_values_status = {}
        self.info_values_coap = {}
        self._state_cfg = None
        self.state_status = None
        self.state_coap = None
        self._channel = 0
        self.cb_updated = []
        self.need_update = False

    def raise_updated(self, force=False):
        if not force and not self.need_update:
            return
        self.need_update = False
        for callback in self.cb_updated:
            callback(self)

    def _fmt_info_value(self, value, cfg, prefix):
        fmt_list = cfg.get(ATTR_FMT, None)
        if type(fmt_list) is dict:
            fmt_list = fmt_list.get(prefix)
        if fmt_list:
            if not type(fmt_list) is list:
                fmt_list = [fmt_list]
            for fmt in fmt_list:
                if fmt is None:
                    continue
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
                    value = value[ch]
                else:
                    value = value.get(key, None)
        return value

    def _update_state(self, status, cfg):
        value = self._get_status_value(status, cfg)
        if value is not None:
            value = self._fmt_info_value(value, cfg, SRC_STATUS)
            self._set_state(value, SRC_STATUS)
            if self.lazy_load:
                self.block.parent.callback_add_device(self)

    def _update_info_value(self, name, status, cfg):
        value = self._get_status_value(status, cfg)
        if value is not None:
            value = self._fmt_info_value(value, cfg, SRC_STATUS)
            self.set_info_value(name, value, SRC_STATUS)
            # if self.info_values.get(name) != value:
            #     self.info_values[name] = value
            #     self.need_update = True
            # self.info_values_updated[name] = datetime.now()
            # self.info_values_status[name] = value

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
                    value = self._fmt_info_value(value, cfg, SRC_COAP)
                    return value
        return None

    def __update_info_values_coap(self, payload, cfg):
        for name, cfg in cfg.items():
            value = self._get_coap_value(cfg, payload)
            self.set_info_value(name, value, SRC_COAP)
            # if value is not None:
            #     self.info_values_updated[name] = datetime.now()
            #     self.info_values_coap[name] = value
            #     if self.info_values.get(name) != value:
            #         self.info_values[name] = value
            #         self.need_update = True

    def _set_state(self, new_state, src):
        if not new_state is None:
            if src == SRC_COAP:
                self.state_coap = new_state
            if src == SRC_STATUS:
                self.state_status = new_state
            if self.state != new_state:
                self.state = new_state
                self.need_update = True

    def _update_info_values_coap(self, payload, extra_info_value_cfg=None):
        if self._state_cfg:
            new_state = self._get_coap_value(self._state_cfg, payload)
            self._set_state(new_state, SRC_COAP)
        if extra_info_value_cfg:
            self.__update_info_values_coap(payload, extra_info_value_cfg)
        if self._info_value_cfg:
            self.__update_info_values_coap(payload, self._info_value_cfg)

    #Todo: remove
    def coap_get(self, payload, pos_list, default=None, channel=None):
        if pos_list is None:
            return default
        if not type(pos_list) is list:
            pos_list = [pos_list]
        for _pos in pos_list:
            ch = channel or self._channel or 0
            if _pos < 1000:
                pos = _pos + 10 * ch
            else:
                pos = _pos + 100 * ch
            if pos in payload:
                return payload[pos]
        return default

    def set_info_value(self, name, value, src):
        if value is None:
            return
        if self.info_values.get(name) != value:
            self.need_update = True
            self.info_values[name] = value
        self.info_values_updated[name] = datetime.now()
        if src == SRC_STATUS:
            self.info_values_status[name] = value
        elif src == SRC_COAP:
            self.info_values_coap[name] = value

