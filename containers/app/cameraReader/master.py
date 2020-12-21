import cv2
import socket
import sys
import struct
import pickle
import queue
import threading

receivedFrameQ = queue.Queue()

resQ = queue.Queue()


def receiveFrame():
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    host = "0.0.0.0"
    port = 9999
    serversocket.bind((host, port))
    serversocket.listen(5)
    clientsocket, _ = serversocket.accept()

    while True:
        print("Receiving frames")
        data = b""
        payload_size = struct.calcsize(">L")
        while len(data) < payload_size:
            data += clientsocket.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += clientsocket.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        receivedFrameQ.put(frame)

        resFrame = resQ.get()
        _, frame_png = cv2.imencode('.jpg', resFrame)
        data = pickle.dumps(frame_png, 0)
        clientsocket.sendall(struct.pack(">L", len(data)) + data)


def forwardFrame():
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    host = "0.0.0.0"
    port = 9998
    serversocket.bind((host, port))
    serversocket.listen(5)
    clientsocket, addr = serversocket.accept()

    print("Worker connected",  addr)

    while True:
        print("Forwarding frames")
        frame = receivedFrameQ.get()
        cv2.imshow("Master Face Detection", frame)
        if cv2.waitKey(1) == ord('q'):
            break
        _, frame_png = cv2.imencode('.jpg', frame)
        data = pickle.dumps(frame_png, 0)
        clientsocket.sendall(struct.pack(">L", len(data)) + data)

        
        data = b""
        payload_size = struct.calcsize(">L")
        while len(data) < payload_size:
            data += clientsocket.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += clientsocket.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        cv2.imshow("Master Face Detection", frame)
        if cv2.waitKey(1) == ord('q'):
            break
        resQ.put(frame)


if __name__ == "__main__":
    threading.Thread(target=receiveFrame).start()
    threading.Thread(target=forwardFrame).start()
