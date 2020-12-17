# ref: https://gist.github.com/kittinan/e7ecefddda5616eab2765fdb2affed1b
import socket
import sys
import base64
import cv2
import struct
import pickle
import numpy as np


def serve():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = sys.argv[1]
    port = int(sys.argv[2])
    s.connect((host, port))
    handle(s, host, port)


def handle(s, host, port):
    data = b""
    payload_size = struct.calcsize(">L")

    while True:

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

        cv2.imshow('Video Stream From %s:%d' % (host, port), frame)

        if cv2.waitKey(1) == ord('q'):
            break


if __name__ == "__main__":
    serve()
