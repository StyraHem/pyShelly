# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except

import json
import time
import urllib
import threading
from datetime import datetime, timedelta

from .compat import s
from .const import LOGGER

try:
    import http.client as httplib
except:
    import httplib

class Cloud():
    def __init__(self, server, key):
        self.auth_key = key
        self.server = server
        self._last_update = None
        self._stopped = threading.Event()
        self.update_interval = timedelta(minutes=1)
        self._device_list = None
        self._room_list = None
        self._cloud_thread = None
        self._last_post = datetime.now()

    def start(self):
        self._cloud_thread = threading.Thread(target=self._update_loop)
        self._cloud_thread.name = "Cloud"
        self._cloud_thread.daemon = True
        self._cloud_thread.start()

    def stop(self):
        self._stopped.set()

    def _update_loop(self):
        while not self._stopped.isSet():
            try:
                if self._last_update is None or \
                    datetime.now() - self._last_update \
                                    > self.update_interval:
                    self._last_update = datetime.now()
                    self._device_list = self.get_device_list()
                    self._room_list = self.get_room_list()
                else:
                    time.sleep(5)
            except Exception as ex:
                LOGGER.error("Error update cloud, %s", ex)

    def _post(self, path, params=None):
        while datetime.now() - self._last_post < timedelta(seconds=2):
            time.sleep(1)
        self._last_post = datetime.now()

        json_body = None
        params = params or {}
        try:
            conn = httplib.HTTPSConnection(self.server, timeout=5)
            headers = {'Content-Type' : 'application/x-www-form-urlencoded'}

            params["auth_key"] = self.auth_key
            conn.request("POST", "/" + path, urllib.parse.urlencode(params),
                         headers)
            resp = conn.getresponse()

            if resp.status == 200:
                body = resp.read()
                #LOGGER.debug("Body: %s", body)
                json_body = json.loads(s(body))
            else:
                print(resp.read())
        except Exception as ex:
            LOGGER.debug("Error connect cloud, %s", ex)
        finally:
            if conn:
                conn.close()

        return json_body

    def get_device_name(self, _id):
        if self._device_list and _id in self._device_list:
            dev = self._device_list[_id]
            name = dev['name']
            try:
                room_id = dev['room_id']
                if room_id in self._room_list:
                    name += ' (' + self._room_list[room_id]['name'] + ')'
            except:
                pass
            return name

    def get_device_list(self):
        return self._post("interface/device/list")['data']['devices']

    def get_status(self):
        self._post("device/all_status")

    def get_room_list(self):
        resp = self._post("interface/room/list")
        return resp['data']['rooms']

    def get_list_xxx(self):
        rooms = self.get_room_list()
        time.sleep(2)
        resp = self._post("interface/device/list")

        for _id, device in resp['data']['devices'].items():
            room_id = device['room_id']
            LOGGER.info("********** " + device["name"] + " " +
                        rooms[room_id]['name'])

        return resp['data']['devices']
