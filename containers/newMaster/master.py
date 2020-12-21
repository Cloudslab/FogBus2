import eventlet
import socketio
import logging

from logger import get_logger
from registry import Registry, RegistryNamespace
from datatype import Master, NodeSpecs
from message import Message


class FogMaster:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def run(self):
        logger = get_logger('Master', logging.INFO)

        sio = socketio.Server()
        app = socketio.WSGIApp(sio, static_files={
            '/': {'content_type': 'text/html', 'filename': 'html/index.html'}
        })
        sio.register_namespace(RegistryNamespace(
            '/registry', sio=sio, logger=logger))

        logger.info("[*] Master serves at: %s:%d" % (self.host,  self.port))
        eventlet.wsgi.server(eventlet.listen((self.host,  self.port)),
                             app, log_output=False)


if __name__ == '__main__':
    master = FogMaster('', 5000)
    master.run()
