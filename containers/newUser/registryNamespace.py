import logging
import socketio
from logger import get_logger
from message import Message


class RegistryNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.connected = False
        self.userID = None
        self.logger = get_logger("UserRegistry", logLevel)

    def on_connect(self):
        self.connected = True
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.connected = False
        self.logger.info("[!] Disconnected.")

    def register(self):
        message = {'role': 'user'}
        messageEncrypted = Message.encrypt(message)
        self.emit('register', messageEncrypted)

    def on_registered(self, message):
        userID = Message.decrypt(message)
        self.userID = userID
