import logging
import socketio
from logger import get_logger
from message import Message


class TaskNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.isConnected = False
        self.canRegister = False
        self.isRegistered = False
        self.userID = None
        self.logger = get_logger("UserTask", logLevel)

    def on_connect(self):
        self.isConnected = True
        self.register()
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.isConnected = False
        self.logger.info("[!] Disconnected.")

    def setUserID(self, userID: int):
        self.userID = userID
        self.canRegister = True

    def submit(self, appID: int, dataID: int):
        message = {'userID': self.userID, 'appID': appID, 'dataID': dataID}
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
        taskID = messageDecrypted["taskID"]
        appID = messageDecrypted["appID"]
        resultID = messageDecrypted["resultID"]
        dataID = messageDecrypted["dataID"]
        self.logger.debug("Received TaskID-%d, Result-%d, dataID-%d, appID-%d", taskID, resultID, dataID, appID)

    def register(self):
        while not self.canRegister:
            pass
        message = {'userID': self.userID, 'role': 'user'}
        messageEncrypted = Message.encrypt(message)
        self.emit('register', data=messageEncrypted)

    def on_registered(self, message):
        messageDecrypted = Message.decrypt(message)
        userID = messageDecrypted['userID']
        if userID == self.userID:
            self.isRegistered = True