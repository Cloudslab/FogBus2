import logging
import socketio
import threading
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


class TaskNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.connected = False
        self.userID = None
        self.logger = get_logger("UserTask", logLevel)

    def on_connect(self):
        self.connected = True
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.connected = False
        self.logger.info("[!] Disconnected.")

    def submit(self, appID: int, dataID: int):
        message = {'appID': appID, 'dataID': dataID}
        messageEncrypted = Message.encrypt(message)
        self.emit('submit', messageEncrypted)
        self.logger.debug("Submitted Task appID: %d, dataID: %d", appID, dataID)

    def on_submitted(self, message):
        messageDecrypted = Message.decrypt(message)
        taskID = messageDecrypted["taskID"]
        appID = messageDecrypted["appID"]
        dataID = messageDecrypted["dataID"]
        self.logger.debug("Received Task-%d -> appID: %d, dataID: %d", taskID, appID, dataID)

    def on_result(self, message):
        messageDecrypted = Message.decrypt(message)
        resultID = messageDecrypted["resultID"]
        dataID = messageDecrypted["dataID"]
        self.logger.debug("Received Result-%d -> dataID-%d", resultID, dataID)


class Broker:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('UserSideBroker', logLevel)
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.registryNamespace = RegistryNamespace('/registry', logLevel=logLevel)
        self.taskNamespace = TaskNamespace('/task', logLevel=logLevel)

    def run(self):
        threading.Thread(target=self.connect).start()
        while not self.taskNamespace.connected or \
                not self.registryNamespace.connected:
            pass
        self.registryNamespace.register()
        while self.registryNamespace.userID is None:
            pass
        self.taskNamespace.userID = self.registryNamespace.userID
        self.logger.info("Got userID-%d", self.taskNamespace.userID)

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.host, self.port))
        self.logger.info("[*] Connected to namespaces.")
        self.sio.wait()


if __name__ == '__main__':
    broker = Broker('http://127.0.0.1', 5000, logLevel=logging.DEBUG)
    broker.run()
    broker.taskNamespace.submit(1, 88)
