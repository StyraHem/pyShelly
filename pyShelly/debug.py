import socket
import threading
import json
import sys
from io import StringIO

from .loop import Loop

from .const import (
    LOGGER
)

class Debug_connection(Loop):
    def __init__(self, parent, connection, client_address):
        super(Debug_connection, self).__init__("Debug connection", parent._root)
        self._debug_server = parent
        self._connection = connection
        self._client_address = client_address
        self.state = 0
        self.cmd = ''
        self._locals = {'root':self._debug_server._root}
        self._globals = {}
        self.start_loop()

    def loop_stopped(self):
        try:
            self._connection.close()
        except:
            pass
        try:
            self._mqt_debug_servert_server._connections.remove(self)
        except:
            pass

    def loop(self):
        if self.state == 0:
            self._connection.send(b"> ")
            self.state = 1
        if self.state == 1:
            try:
                char = self._connection.recv(1).decode()
            except socket.timeout:
                pass
            except:
                LOGGER.exception("Error receiving debug command")
                self.stop_loop()
            if char in ['\r', '\n']:
                if not self.cmd:
                    return
                elif self.cmd == 'exit':
                    self.stop_loop()
                else:                         
                    old_stdout = sys.stdout
                    redirected_output = sys.stdout = StringIO()
                    try:
                        exec(self.cmd, self._globals, self._locals)
                        res = redirected_output.getvalue()
                        self._connection.send(res.encode()  + b"\r\n")                        
                    except Exception as ex:
                        self._connection.send(str(ex).encode() + b"\r\n")
                    finally:
                        sys.stdout = old_stdout
                        self.cmd = ''
                        self.state = 0
            else:
                self.cmd += char
        
class Debug_server(Loop):

    def __init__(self, root):
        super(Debug_server, self).__init__("Debug server", root)
        self._root = root
        self._socket = None
        self._connections = []
        self.start_loop()

    def loop_started(self):
        self._init_socket()

    def _init_socket(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self._root.bind_ip, 7212))
        sock.listen(1)
        self._socket = sock

    def loop(self):
        # Wait for a connection
        connection, client_address = self._socket.accept()
        conn = Debug_connection(self, connection, client_address)
        self._connections.append(conn)

    def loop_stopped(self):
        if self._socket:
            self._socket.close()


# import socket
# import sys

# def main():
#     host = ""
#     port = 50000
#     backlog = 5
#     size = 1024
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.bind((host, port))
#     sock.listen(backlog)
#     while True:
#         client, address = sock.accept()
#         test.log("Client connected.")
#         while True:
#             data = client.recv(size).rstrip()
#             if not data:
#                 continue
#             test.log("Received command: %s" % data)
#             if data == "disconnect":
#                 test.log("Client disconnected.")
#                 client.send(data)
#                 client.close()
#                 break
#             if data == "exit":
#                 test.log("Client asked server to quit")
#                 client.send(data)
#                 client.close()
#                 return

#             test.log("Executing command: %s" % data)
#             try:
#                 exec(data)
#             except Exception, err:
#                 test.log("Error occured while executing command: %s" % (
#                         data), str(err))