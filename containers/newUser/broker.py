import logging
import socketio
import threading
from logger import get_logger


class RegistryNamespace(socketio.ClientNamespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass


class TaskNamespace(socketio.ClientNamespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass


class Broker:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.logger = get_logger('Broker', logLevel)
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.registryNamespace = RegistryNamespace('/registry')
        self.taskNamespace = TaskNamespace('/task')

    def run(self):
        threading.Thread(target=self.connect).start()

    def connect(self):
        self.sio.register_namespace(self.registryNamespace)
        self.sio.register_namespace(self.taskNamespace)
        self.sio.connect('%s:%d' % (self.host, self.port))
        self.logger.info("[*] Connected to namespaces.")
        self.sio.wait()


if __name__ == '__main__':
    broker = Broker('http://127.0.0.1', 5000)
    broker.run()
