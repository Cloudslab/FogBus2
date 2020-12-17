import cv2
import socket
import sys
import struct
import pickle


def camera(clientsocket):
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FPS, 30)
    while True:
        ret, frame = cam.read()
        if not ret: 
            break
        res, frame_png = cv2.imencode('.jpg', frame)

        data = pickle.dumps(frame_png, 0)
        clientsocket.sendall(struct.pack(">L", len(data)) + data)

    print("[*] Done.")

def socketSetver():
    serversocket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM) 
    host = "0.0.0.0"
    port = 9999

    print("[*] Service addr: %s:%d" % (host, port))
    serversocket.bind((host, port))

    serversocket.listen(5)

    clientsocket, addr = serversocket.accept()      

    print("[-] Client addr: %s" % str(addr))
    camera(clientsocket)

    

if __name__ == "__main__":
    socketSetver()