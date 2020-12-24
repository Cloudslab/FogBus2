import logging
import socketio
from logger import get_logger
from message import Message


class TaskNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.isConnected = False
        self.isRegistered = False
        self.workerID = None
        self.logger = get_logger("WorkerTask", logLevel)

    def on_connect(self):
        self.isConnected = True
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.isConnected = False
        self.logger.info("[!] Disconnected.")

    def on_task(self, message):
        decryptedMessage = Message.decrypt(message)
        taskID = decryptedMessage["taskID"]
        appID = decryptedMessage["appID"]
        dataID = decryptedMessage["dataID"]
        self.logger.debug("Received Task-%d, appID: %d, dataID: %d", taskID, appID, dataID)

    def finish(self, taskID, dataID, resultID):
        message = {'workerID': self.workerID, 'taskID': taskID, 'dataID': dataID, 'resultID': resultID}
        messageEncrypted = Message.encrypt(message)
        self.emit('finish', messageEncrypted)
        self.logger.debug("Finished Task-%d, dataID: %d, resultID: %d", taskID, dataID, resultID)

    def on_result(self, message):
        messageDecrypted = Message.decrypt(message)
        resultID = messageDecrypted["resultID"]
        dataID = messageDecrypted["dataID"]
        self.logger.debug("Received Result-%d -> dataID-%d", resultID, dataID)

    def register(self):
        message = {'workerID': self.workerID, 'role': 'worker'}
        messageEncrypted = Message.encrypt(message)
        self.emit('register', data=messageEncrypted)

    def on_registered(self, message):
        messageDecrypted = Message.decrypt(message)

        workerID = messageDecrypted['workerID']
        if workerID == self.workerID:
            self.isRegistered = True
