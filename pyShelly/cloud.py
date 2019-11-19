# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except

import json
import time
import urllib

from .compat import s
from .const import LOGGER

try:
    import http.client as httplib
except:
    import httplib


class Cloud():
    def __init__(self):
        self.cloud_auth_key = "YTA1dWlk673E6CDA3DCCCBB3156AFA348A8734B73D" + \
                            "CD5EE4799F8E0541FD8EC94622BABB49AB62F1862313F4"
        self.cloud_server = "shelly-5-eu.shelly.cloud"

        #self._list = self.get_list()

    def _post(self, path, params=None):
        json_body = None
        params = params or {}
        try:
            LOGGER.info("-----------------------------------")
            conn = httplib.HTTPSConnection(self.cloud_server, timeout=5)
            headers = {'Content-Type' : 'application/x-www-form-urlencoded'}

            params["auth_key"] = self.cloud_auth_key
            conn.request("POST", "/" + path, urllib.parse.urlencode(params), headers)
            resp = conn.getresponse()

            if resp.status == 200:
                body = resp.read()
                LOGGER.debug("Body: %s", body)
                json_body = json.loads(s(body))
            else:
                print(resp.read())

            conn.close()
        except Exception:
            pass

        return json_body

    def get_list(self):
        self._post("device/list")

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
            LOGGER.info("********** " + device["name"] + " " + rooms[room_id]['name'])

        return resp['data']['devices']
