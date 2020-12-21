import socketio
from datatype import NodeSpecs
from message import Message

sio = socketio.Client()


@sio.event(namespace='/registry')
def connect():
    print('connection established')


@sio.event(namespace='/registry')
def id(data):
    print('registered', data)


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
