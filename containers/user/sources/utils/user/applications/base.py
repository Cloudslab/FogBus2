import threading
from abc import abstractmethod
from queue import Queue
from threading import Event
from time import time
from typing import Any
from typing import Tuple

import cv2

from ...component.basic import BasicComponent
from ...types import SequenceMedian


class ApplicationUserSide:

    def __init__(
            self,
            basicComponent: BasicComponent,
            appName: str,
            videoPath: str = None,
            targetHeight: int = 640,
            showWindow: bool = True,
            pressSpaceToStart: bool = False):
        self.pressSpaceToStart = pressSpaceToStart
        self.basicComponent = basicComponent
        self.appName = appName
        if appName in {
            'FaceDetection',
            'FaceAndEyeDetection',
            'ColorTracking',
            'VideoOCR'}:
            self.sensor = cv2.VideoCapture(0) if videoPath is None \
                else cv2.VideoCapture(videoPath)
        else:
            self.sensor = None
        self.resultForActuator: Queue = Queue()
        self.dataToSubmit: Queue = Queue()
        self.targetHeight = targetHeight
        self.showWindow: bool = showWindow
        self.videoPath: str = videoPath
        self.responseTime = SequenceMedian(maxRecordNumber=10)
        self.responseTimeCount = 0
        self.windowFrameQueue = None
        if self.showWindow:
            self.windowFrameQueue: Queue[Tuple[str, Any]] = Queue(1)
        self.interval = 1 / 60
        self.canStart: Event = Event()
        if not self.pressSpaceToStart:
            self.canStart.set()
        self.startTime = time() * 1000

    def resizeFrame(self, frame):
        width = frame.shape[1]
        height = frame.shape[0]
        resizedWidth = int(width * self.targetHeight / height)
        return cv2.resize(frame, (resizedWidth, self.targetHeight))

    def start(self):
        threading.Thread(target=self._run).start()

    @staticmethod
    def _run():
        raise NotImplementedError

    @abstractmethod
    def prepare(self):
        pass
