import socketio
import logging
from datatype import Worker, NodeSpecs
from message import Message

class Registry:

    def __init__(self):
        self.id = 0
        self.workers = {}

    def addWoker(self, sid:str, nodeSpecs:NodeSpecs):
        self.id += 1
        self.workers[self.id] = Worker(self.id, sid, nodeSpecs)
        return self.id

    def remove(self, workerID):
        del self.workers[workerID]


class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, logger=logging, sio = None):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = Registry()
        self.logger = logger
        self.sio = sio

    def on_connect(self, socketID, environ):
        pass

    def on_register(self, socketID, msg):
        nodeSpecs = Message.decrypt(msg)
        workerID = self.registry.addWoker(socketID, nodeSpecs)
        self.sio.emit("id",  to=socketID, data=workerID, namespace='/registry')
        self.logger.info("[*] Worker-%d joined: \n%s" % (workerID, nodeSpecs.info()))

    def on_disconnect(self, socketID):
        print('disconnect ', socketID)

if __name__ == "__main__":
    print("[*] Test Registry")
    registry = Registry()
