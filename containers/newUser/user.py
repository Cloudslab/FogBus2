import cv2
import socket
import sys
import logging
import struct
import pickle
import queue
import threading

from logger import get_logger
from broker import Broker
from dataManager import DataManager


class User:

    def __init__(self,
                 broker: Broker,
                 dataManager: DataManager,
                 logLevel=logging.DEBUG):
        self.logger = get_logger('User', logLevel)
        self.broker: Broker = broker
        self.dataManager: DataManager = dataManager
        self.app = app

    @staticmethod
    def getFrames(self, framesQueue: queue.Queue, videoStream: cv2.VideoCapture):
        while True:
            print("Sending frames")
            ret, frame = videoStream.read()
            if not ret:
                break
            framesQueue.put(frame)

    def run(self):
        self.broker.run()
        self.dataManager.run()

    def input(self):
        framesQueue = queue.Queue()
        threading.Thread(target=self.getFrames, args=(framesQueue,)).start()

    def output(self):
        pass


if __name__ == "__main__":
    broker = Broker('http://127.0.0.1', 5000)
    dataManager = DataManager(host='0.0.0.0',
                              portSending=5001,
                              portReceiving=5002,
                              logLevel=logging.DEBUG)
    user = User(broker=broker, dataManager=dataManager)
