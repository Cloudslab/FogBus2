import socket
import struct
import socketserver
import threading
from message import encrypt, decrypt
from typing import Any


class Connection:
    def __init__(self, ip: str, port: int):
        self.ip: str = ip
        self.port: int = port
        self.__payloadSize = struct.calcsize('>L')

    def send(self, data: Any, retries: int = 3):
        try:
            clientSocket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM)
            clientSocket.connect((self.ip, self.port))
            encryptData = encrypt(data)
            package = struct.pack(">L", len(encryptData)) + encryptData
            clientSocket.sendall(package)

        except OSError:
            self.send(data=data, retries=retries - 1)


class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class RequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(1024), 'ascii')
        cur_thread = threading.current_thread()
        response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        self.request.sendall(response)


if __name__ == '__main__':
    pass
