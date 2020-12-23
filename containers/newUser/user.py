import socketio
import cv2
import socket
import threading
import struct
from message import Message
from typing import Any


def run():
    sio = socketio.Client()

    @sio.event(namespace='/registry')
    def connect():
        print('connection established')

    @sio.event(namespace='/registry')
    def task(data):
        print("task comes")

    @sio.event(namespace='/registry')
    def disconnect():
        print('disconnected from server')

    def emit(sio: socketio.Client, event: str, message: bytes, namespace: str):
        pass

    sio.connect('http://127.0.0.1:5000', namespaces=['/registry', '/task'])
    print(sio.connection_namespaces)
    msg = {"role": "user"}
    sio.emit('register', Message.encrypt(msg), namespace='/registry')

    frame = 1
    camera = cv2.VideoCapture(0)
    _, frame = camera.read()
    camera.release()
    msg = {"userID": 1, "inputData": frame, "partition": 1, "total": 100}
    emit(sio, 'submit', Message.encrypt(msg), namespace='/task')

    sio.wait()


def sendFrame():
    cam = cv2.VideoCapture(0)
    _, frame = cam.read()
    cam.release()
    _, frameJpg = cv2.imencode('.jpg', frame)
    sendMessage(frameJpg)


def sendMessage(data: Any):
    dataEncrypted = Message.encrypt(data)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 5001
    s.connect((host, port))
    s.sendall(struct.pack(">L", len(dataEncrypted)) + dataEncrypted)
    print("done")


if __name__ == '__main__':
    sendFrame()
