import socketio
from datatype import NodeSpecs
from message import Message

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


sio.connect('http://127.0.0.1:5000', namespaces=['/registry', '/task'])
print(sio.connection_namespaces)
msg = {"role": "user"}
sio.emit('register', Message.encrypt(msg), namespace='/registry')

msg = {"userID": 1, "inputData": "inputData"}
sio.emit('submit', Message.encrypt(msg), namespace='/task')

sio.wait()
