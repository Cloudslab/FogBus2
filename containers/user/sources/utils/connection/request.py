from socket import socket

from ..types import Address


class ConnectionRequest:

    def __init__(self, clientSocket: socket, clientAddr: Address):
        self.clientSocket = clientSocket
        self.clientAddr = clientAddr
