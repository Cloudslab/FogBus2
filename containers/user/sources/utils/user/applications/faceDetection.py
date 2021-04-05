from time import sleep
from time import time

import cv2

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class FaceDetection(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent):
        super().__init__(
            appName='FaceDetection',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent)

    def prepare(self):
        pass

    def _run(self):
        self.basicComponent.debugLogger.info(
            'Application is running: %s', self.appName)
        lastReadTime = 0
        while True:
            ret, frame = self.sensor.read()
            if not ret:
                break
            currentTime = time()
            frame = self.resizeFrame(frame)
            self.dataToSubmit.put(frame)
            lastDataSentTime = time()
            faces = self.resultForActuator.get()
            responseTime = (time() - lastDataSentTime) * 1000
            self.responseTime.update(responseTime)
            self.responseTimeCount += 1
            for (x, y, w, h, roi_gray) in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (255, 0, 0),
                    2)
            toSleep = currentTime - lastReadTime
            lastReadTime = currentTime
            if toSleep < self.interval:
                sleep(toSleep)
            if not self.showWindow:
                continue
            self.windowFrameQueue.put(('FaceDetection', frame))
        self.sensor.release()
