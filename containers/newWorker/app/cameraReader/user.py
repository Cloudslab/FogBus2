import cv2
import socket
import sys
import logging
import struct
import pickle
import queue
import threading

from logger import get_logger


class User:

    def __init__(self, logLevel=logging.DEBUG):
        self.logger = get_logger('Broker', logLevel)


def getFrames(framesQueue: queue.Queue, videoStream: cv2.VideoCapture):
    while True:
        print("Sending frames")
        ret, frame = videoStream.read()
        if not ret:
            break
        framesQueue.put(frame)


def run():
    framesQueue = queue.Queue()
    threading.Thread(target=getFrames, args=(framesQueue,)).start()


if __name__ == "__main__":
