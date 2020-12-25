import logging
import socketio
from logger import get_logger
from queue import Queue
from message import Message


class TaskNamespace(socketio.ClientNamespace):
    def __init__(self, namespace=None, logLevel=logging.DEBUG):
        super(TaskNamespace, self).__init__(namespace=namespace)
        self.isConnected = False
        self.canRegister = False
        self.isRegistered = False
        self.userID = None
        self.resultDataQueue: Queue = Queue()
        self.logger = get_logger("User-Task", logLevel)

    def on_connect(self):
        self.isConnected = True
        self.register()
        self.logger.info("[*] Connected.")

    def on_disconnect(self):
        self.isConnected = False
        self.logger.info("[!] Disconnected.")

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

    def setUserID(self, userID: int):
        self.userID = userID
        self.canRegister = True

    def submit(self, appID: int, dataID: int):
        message = {'userID': self.userID, 'appID': appID, 'dataID': dataID}
        messageEncrypted = Message.encrypt(message)
        self.emit('submit', messageEncrypted, callback=self.submitCallback)

    def submitCallback(self, message):
        messageDecrypted = Message.decrypt(message)
        isHandling = messageDecrypted['isHandling']
        if isHandling:
            taskID = messageDecrypted['taskID']
            appID = messageDecrypted['appID']
            dataID = messageDecrypted['dataID']
            self.logger.debug("Submitted task taskID-%d, appID-%d, dataID-%d", taskID, appID, dataID)
        else:
            reason = messageDecrypted['reason']
            appID = messageDecrypted['appID']
            dataID = messageDecrypted['dataID']
            self.logger.debug("Cannot submit appID-%d, dataID-%d because %s", appID, dataID, reason)
            self.resultDataQueue.put(None)

    def on_result(self, message):
        messageDecrypted = Message.decrypt(message)
        resultID = messageDecrypted["resultID"]
        taskID = messageDecrypted["taskID"]
        appID = messageDecrypted["appID"]
        dataID = messageDecrypted["dataID"]
        self.resultDataQueue.put(resultID)
        self.logger.debug("Received resultID-%d, taskID-%d, dataID-%d, appID-%d", resultID, taskID, dataID, appID)
