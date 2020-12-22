import cv2
import socket
import sys
import struct
import pickle
import queue
import threading


def sendFrame():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "192.168.3.49"
    port = 9999
    s.connect((host, port))

    

    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FPS, 30)
    while True:
        print("Sending frames")
        ret, frame = cam.read()
        if not ret:
            break
        _, frame_png = cv2.imencode('.jpg', frame)

        data = pickle.dumps(frame_png, 0)
        s.sendall(struct.pack(">L", len(data)) + data)

        print("Receiving frames")
        data = b""
        payload_size = struct.calcsize(">L")
        while len(data) < payload_size:
            data += s.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += s.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        cv2.imshow("User Face Detection", frame)
        if cv2.waitKey(1) == ord('q'):
            break


if __name__ == "__main__":
    threading.Thread(target=sendFrame).start()
