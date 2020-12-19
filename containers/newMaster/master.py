import eventlet
import socketio
import logging

from logger import get_logger
from registry import Registry
from datatype import Master, NodeSpecs

class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, logger=logging):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = Registry()
        self.logger = logger

    def connect(self, socketID, environ):
        print("connect")
        pass

    def register(self, socketID, t):
        
        workerID = self.registry.addWoker(socketID, NodeSpecs(1, 2, 3, 4))
        sio.emit("id",  to=socketID, data=workerID, )
        logger.info(self.registry.workers)

    def my_message(self, socketID, data):
        print('message ', data)

    def disconnect(self, socketID):
        print('disconnect ', socketID)


if __name__ == '__main__':
    logger = get_logger('Master', logging.INFO)

    sio = socketio.Server()
    app = socketio.WSGIApp(sio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'html/index.html'}
    })
    sio.register_namespace(RegistryNamespace('/registry', logger))

    host = ''
    port = 5000
    logger.info("[*] Master serves at: %s:%d" % (host, port))
    eventlet.wsgi.server(eventlet.listen((host, port)),
                         app, log_output=False)
