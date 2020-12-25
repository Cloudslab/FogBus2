import logging
import socketio
from logger import get_logger
from datatype import NodeSpecs
from message import Message


class RegistryNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.connected = False
        self.workerID = None
        self.isRegistered = False
        self.logger = get_logger("Worker-Registry", logLevel)

    def on_connect(self):
        self.connected = True
        self.register()
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.connected = False
        self.logger.info("[!] Disconnected.")

    def register(self):
        message = {'role': 'worker', 'nodeSpecs': NodeSpecs(1, 2, 3, 4)}
        if self.workerID is not None:
            message['workerID'] = self.workerID
        messageEncrypted = Message.encrypt(message)
        self.emit('register', messageEncrypted)

    def on_registered(self, message):
        workerID = Message.decrypt(message)
        self.workerID = workerID
        self.isRegistered = True
