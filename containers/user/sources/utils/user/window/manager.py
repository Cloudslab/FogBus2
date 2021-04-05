from queue import Queue
from threading import Event
from time import sleep
from time import time
from typing import Any
from typing import Callable
from typing import Tuple

import cv2

from ...component.basic import BasicComponent


class WindowManager:
    def __init__(
            self,
            basicComponent: BasicComponent,
            frameQueue: Queue[Tuple[str, Any]],
            prepareWindows: Callable,
            canStart: Event,
            pressSpaceToStart=False,
            interval: float = 1 / 60):
        self.basicComponent = basicComponent
        self.interval = interval
        self.pressSpaceToStart = pressSpaceToStart
        self.prepareWindows = prepareWindows
        self.frameQueue = frameQueue
        self.prepareWindows()
        self.canStart: Event = canStart

    def run(self):
        lastUpdatedTime = time()
        while True:
            windowName, frame = self.frameQueue.get()
            currentTime = time()
            timeDiff = currentTime - lastUpdatedTime
            if timeDiff < self.interval:
                sleep(self.interval - timeDiff)
            lastUpdatedTime = currentTime
            cv2.imshow(windowName, frame)
            if not self.pressSpaceToStart:
                cv2.waitKey(10)
                continue
            while True:
                k = cv2.waitKey(32)
                if k != 32:
                    sleep(.1)
                    continue
                self.basicComponent.debugLogger.debug(k)

                self.pressSpaceToStart = False
                self.canStart.set()
                break
            continue
