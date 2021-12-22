import socket
import uuid
import threading
import json
import websocket
from datetime import datetime

from .utils import error_log

from .const import (
    LOGGER, SHELLY_TYPES
)

class WebSocket:
    def __init__(self, block):
        self.block = block
        self.send_id = 1
        self.connected = False
        self.ws = None
        self.uid = uuid.uuid4().hex[:8]
        self.last_try_connect = None
        self.try_connect = 0
        self.thread = None
        #websocket.enableTrace(True)
        self.check()
    def on_open(self, ws):
        #print("Connected Websocket", self.block.ip_addr)
        self.connected = True
        self.try_connect = 0
        self.send("Shelly.GetStatus")
    def on_close(self, ws, close_status_code, close_msg):        
        self.connected = False
        #print("Websocket closed", self.block.ip_addr)
    def on_message(self, ws, message):
        json_msg = json.loads(message)
        if "error" in json_msg:
            error = json_msg["error"]["message"];
            json_error = json.loads(error)
            if "auth_type" in json_error:
                error_log("Restrict login is not supported for Plus/Pro devices.")
            else:   
                error_log("WS error: {0}", error)
        else:
            self.block.update_rpc(json_msg["params"] if "params" in json_msg else json_msg["result"])
    def send(self, method, params=None):
        if not self.connected:
            return False
        try:
            data = {
                "id": self.send_id,
                "src": "s4h_ws_" + self.uid,
                "method" : method,
                "params" : params
            }
            self.send_id+=1
            self.ws.send(json.dumps(data))
            return True
        except:
            return False
    def ws_thread(self):
        self.try_connect += 1
        self.ws = websocket.WebSocketApp(
            "ws://" + self.block.ip_addr + "/rpc",
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close
        )
        self.ws.run_forever(ping_interval=60)
        #print("Close")

    def check(self):
        if self.connected:
            return
        if self.block.ip_addr:
            if self.ws:
                self.ws.close()
            if self.try_connect >= 1:
                diff = (datetime.now()-self.last_try_connect).total_seconds()
                if diff < 30 or (diff < 60 and self.try_connect >= 5):
                    return
            self.last_try_connect = datetime.now()
            #_thread.start_new_thread(self.ws_thread, ())
            self.thread = threading.Thread(name="S4H-WebSocket", target=self.ws_thread);
            self.thread.daemon = True
            self.thread.start(); 
            