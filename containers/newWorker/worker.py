import socketio
import cv2
import threading
from queue import Queue
from datatype import NodeSpecs
from message import Message


sio = socketio.Client()

q = Queue()


def process():

    data = q.get()
    frame = Message.decrypt(data)
    face_cascade = cv2.CascadeClassifier(
        './cascade/haar-face.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for(x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    print("done")
    sio.emit('finish', Message.encrypt(
        frame), namespace='/registry')


threading.Thread(target=process).start()


@sio.event(namespace='/registry')
def connect():
    print('connection established')


@sio.event(namespace='/registry')
def task(data):
    print("task comes")
    q.put(data)


@sio.event(namespace='/registry')
def my_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})


@sio.event(namespace='/registry')
def disconnect():
    print('disconnected from server')


sio.connect('http://127.0.0.1:5000', namespaces=['/registry'])
print(sio.connection_namespaces)
sio.emit('register', Message.encrypt(
    NodeSpecs(1, 1, 1, 1)), namespace='/registry')
sio.wait()
