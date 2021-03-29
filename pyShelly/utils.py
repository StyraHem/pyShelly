# -*- coding: utf-8 -*-
# pylint: disable=broad-except, bare-except

import base64
import traceback
import json
import socket
from datetime import datetime
from .compat import s
try:
    import http.client as httplib
except:
    import httplib

from .const import (
    LOGGER
)

class timer():
    def __init__(self, interval):
        self._interval = interval
        self._last_time = None
    def check(self):
        if self._interval is not None:
            now = datetime.now()
            if self._last_time is None or \
                    now - self._last_time > self._interval:
                self._last_time = now
                return True
        return False

def exception_log(ex, _msg, *args):
    """Log exception"""
    msg = _msg.format(*args)
    try:
        msg += ", " + str(ex) + ", " + traceback.format_exc()
        LOGGER.exception(msg)
    except Exception as ex:
        LOGGER.error("Exception log error %s", ex)

def shelly_http_get(host, url, username, password, log_error=True):
    """Send HTTP GET request"""
    res = ""
    success = False
    conn = None
    try:
        LOGGER.debug("http://%s%s", host, url)
        conn = httplib.HTTPConnection(host, timeout=5)
        headers = {"Connection": "close"}        
        conn.request("GET", url, None, headers)
        resp = conn.getresponse()

        if resp.status == 401 and \
            username is not None and password is not None:
                combo = '%s:%s' % (username, password)
                auth = s(
                    base64.b64encode(combo.encode()))  # .replace('\n', '')
                headers["Authorization"] = "Basic %s" % auth
                conn.request("GET", url, None, headers)
                resp = conn.getresponse()

        if resp.status == 200:
            body = resp.read()
            #LOGGER.debug("Body: %s", body)
            res = json.loads(s(body))
            success = True
            LOGGER.debug("http://%s%s - Ok", host, url)
        else:
            res = "Error, {} {} http://{}{}".format(
                resp.status, resp.reason, host, url)
            LOGGER.warning(res)
    except Exception as ex:
        success = False
        if (type(ex) == socket.timeout):
          msg = "Timeout connecting to http://" + host + url
          try:
            res = socket.gethostbyaddr(host)[0]
            msg += " [" + res + "]"
          except Exception as ex:
            pass
          LOGGER.error(msg)
        else:
          res = str(ex)
          if log_error:
              exception_log(ex, "Error http GET: http://{}{}", host, url)
          else:
              LOGGER.debug("Fail http GET: %s %s %s", host, url, ex)
    finally:
        if conn:
            conn.close()

    return success, res

def notNone(value, default):
    return default if value is None else value
