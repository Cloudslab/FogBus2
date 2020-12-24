import logging
import socketio
import threading
from logger import get_logger
from datatype import NodeSpecs
from message import Message


class RegistryNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.connected = False
        self.workerID = None
        self.logger = get_logger("WorkerRegistry", logLevel)

    def on_connect(self):
        self.connected = True
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.connected = False
        self.logger.info("[!] Disconnected.")

    def register(self):
        message = {'role': 'worker', 'nodeSpecs': NodeSpecs(1, 2, 3, 4)}
        messageEncrypted = Message.encrypt(message)
        self.emit('register', messageEncrypted)

    def on_registered(self, message):
        workerID = Message.decrypt(message)
        self.workerID = workerID


class TaskNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.isConnected = False
        self.workerID = None
        self.logger = get_logger("WorkerTask", logLevel)

    def on_connect(self):
        self.isConnected = True
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.isConnected = False
        self.logger.info("[!] Disconnected.")

    def on_workOn(self, message):
        decryptedMessage = Message.decrypt(message)
        taskID = decryptedMessage["taskID"]
        appID = decryptedMessage["appID"]
        dataID = decryptedMessage["dataID"]
        self.logger.debug("Working on Task-%d, appID: %d, dataID: %d", taskID, appID, dataID)

    def finish(self, taskID, dataID, resultID):
        message = {'taskID': taskID, 'dataID': dataID, 'resultID': resultID}
        messageEncrypted = Message.encrypt(message)
        self.emit('finish', messageEncrypted)
        self.logger.debug("Finished Task-%d, dataID: %d, resultID: %d", taskID, dataID, resultID)

    def on_result(self, message):
        messageDecrypted = Message.decrypt(message)
        resultID = messageDecrypted["resultID"]
        dataID = messageDecrypted["dataID"]
        self.logger.debug("Received Result-%d -> dataID-%d", resultID, dataID)
        pass


class Broker:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('WorkerSideBroker', logLevel)
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.registryNamespace = RegistryNamespace('/registry', logLevel=logLevel)
        self.taskNamespace = TaskNamespace('/task', logLevel=logLevel)

    def run(self):
        threading.Thread(target=self.connect).start()
        while not self.taskNamespace.isConnected or \
                not self.registryNamespace.connected:
            pass
        self.registryNamespace.register()
        while self.registryNamespace.workerID is None:
            pass
        self.taskNamespace.workerID = self.registryNamespace.workerID
        self.logger.info("Got workerID-%d", self.taskNamespace.workerID)

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.host, self.port))
        self.logger.info("[*] Connected to namespaces.")
        self.sio.wait()


if __name__ == '__main__':
    broker = Broker('http://127.0.0.1', 5000, logLevel=logging.DEBUG)
    broker.run()
