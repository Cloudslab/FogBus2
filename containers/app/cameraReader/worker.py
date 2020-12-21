import cv2
import socket
import sys
import struct
import pickle
import queue
import threading

hanldedFrameQ = queue.Queue()


def getFrame():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "0.0.0.0"
    port = 9998
    client.connect((host, port))
    

    face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')

    while True:
        data = b""
        payload_size = struct.calcsize(">L")
        print("Got frame")
        while len(data) < payload_size:
            data += client.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for(x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow("Worker Face Detection", frame)
        if cv2.waitKey(1) == ord('q'):
            break

        _, frame_png = cv2.imencode('.jpg', frame)
        data = pickle.dumps(frame_png, 0)
        client.sendall(struct.pack(">L", len(data)) + data)


if __name__ == "__main__":

    threading.Thread(target=getFrame).start()
