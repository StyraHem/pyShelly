import socket
import uuid
import threading
import json
import websocket
from datetime import datetime

from .utils import error_log

from .const import (
    LOGGER, SHELLY_TYPES, SRC_WS, SRC_WS_STATUS
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
                # auth: {
                #   "realm": "shellypro4pm-84cca87e48d8",
                #   "username": "admin",
                #   "nonce": 1640195650,
                #   "cnonce": 1640195650468,
                #   "response": "cee1a9eab83de7b33a065b5bae9c695ae39cd40dcc1396af69108b2ad9c77528",
                #   "algorithm": "SHA-256"
                # }
                error_log("Restrict login is not supported for Plus/Pro device ({}, {}, {}).", 
                            self.block.id, self.block.type, self.block.ip_addr)
            else:   
                error_log("WS error: {0}", error)
        else:
            params = "params" in json_msg
            self.block.update_rpc(json_msg["params"] if params else json_msg["result"], SRC_WS if params else SRC_WS_STATUS)
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
            