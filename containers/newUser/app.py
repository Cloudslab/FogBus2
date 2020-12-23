import cv2
import queue
from broker import Broker
from dataManager import DataManager
from typing import Any


class ApplicationUserSide:

    def __init__(self, appID: int, broker: Broker, dataManager: DataManager):
        self.appID: int = appID
        self.broker: Broker = broker
        self.dataManager: DataManager = dataManager
        self.inputDataQueue: queue.Queue = queue.Queue()
        self.inputDataIDQueue: queue.Queue = queue.Queue()
        self.outDataQueue: queue.Queue = queue.Queue()
        self.outDataIDQueue: queue.Queue = queue.Queue()

    def uploadInputData(self):
        videoStream = cv2.VideoCapture(0)
        while True:
            print("Sending frames")
            ret, frame = videoStream.read()
            if not ret:
                break
            self.inputDataQueue.put(frame)

    def downloadOutputData(self):
        while True:
            dataID = self.outDataIDQueue.get()
            self.dataManager.dataIDsToReceive.put(dataID)
            while dataID not in self.dataManager.dataIDsToReceive:

            data = self.dataManager.dataReceived.get()