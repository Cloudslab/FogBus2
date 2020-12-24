import logging
import socketio

from logger import get_logger
from message import Message


class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, registry=None, sio=None, logLevel=logging.DEBUG):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = registry
        self.logger = get_logger("MasterRegistryNamespace", logLevel)
        self.sio: socketio.Server = sio

    def on_register(self, socketID, message):
        messageDecrypted = Message.decrypt(message)
        role = messageDecrypted["role"]
        if role == "user":
            if 'userID' in messageDecrypted:
                userID = messageDecrypted['userID']
                self.registry.users[userID].registrySocketID = socketID
            else:
                userID = self.registry.addUser(registrySocketID=socketID)
            messageEncrypted = Message.encrypt(userID)
            self.emit('registered', room=socketID, data=messageEncrypted)

        elif role == "worker":
            nodeSpecs = messageDecrypted["nodeSpecs"]
            if 'workerID' in messageDecrypted:
                workerID = messageDecrypted['workerID']
                self.registry.workers[workerID].workerSocketID = socketID
            else:
                workerID = self.registry.addWorker(
                    workerSocketID=socketID,
                    nodeSpecs=nodeSpecs)

            messageEncrypted = Message.encrypt(workerID)
            self.emit('registered', room=socketID, data=messageEncrypted)

    def on_exit(self, socketID):
        if socketID in self.registry.usersBySocketID:
            self.logger.info("[*] User-%d exited.", self.registry.usersBySocketID[socketID].workerID)
            self.registry.removeUserBySocketID(socketID)
        else:
            self.logger.info("[*] Worker-%d exited.", self.registry.workersBySocketID[socketID].workerID)
            self.registry.removeWorkerBySocketID(socketID)
