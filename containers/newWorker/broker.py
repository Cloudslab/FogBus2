import logging
import socketio
import threading
from logger import get_logger
from message import Message


class RegistryNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.logger = get_logger("WorkerRegistry", logLevel)

    def on_connect(self):
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.logger.info("[!] Disconnected.")


class TaskNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.logger = get_logger("WorkerTask", logLevel)

    def on_connect(self):
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
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

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.host, self.port))
        self.logger.info("[*] Connected to namespaces.")
        self.sio.wait()


if __name__ == '__main__':
    broker = Broker('http://127.0.0.1', 5000, logLevel=logging.DEBUG)
    broker.run()
