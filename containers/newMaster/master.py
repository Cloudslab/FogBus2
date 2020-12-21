import eventlet
import socketio
import logging

from logger import get_logger
from registry import Registry
from datatype import Master, NodeSpecs
from message import Message


class RegistryNamespace(socketio.Namespace):

    def __init__(self, namespace=None, logger=logging):
        super(RegistryNamespace, self).__init__(namespace=namespace)
        self.registry = Registry()
        self.logger = logger

    def on_connect(self, socketID, environ):
        pass

    def on_register(self, socketID, msg):
        nodeSpecs = Message.decrypt(msg)
        workerID = self.registry.addWoker(socketID, nodeSpecs)
        sio.emit("id",  to=socketID, data=workerID, namespace='/registry')
        logger.info("[*] Worker-%d joined: \n%s" % (workerID, nodeSpecs.info()))

    def on_disconnect(self, socketID):
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
