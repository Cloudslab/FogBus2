from time import sleep
from time import time

import cv2

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class FaceAndEyeDetection(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent):
        super().__init__(
            appName='FaceAndEyeDetection',
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
            for (x, y, w, h, eyes) in faces:
                roi_color = frame[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                for (eyeX, eyeY, eyeW, eyeH) in eyes:
                    cv2.rectangle(roi_color, (eyeX, eyeY),
                                  (eyeX + eyeW, eyeY + eyeH), (0, 0, 255), 2)
                    cv2.circle(
                        roi_color,
                        (int(eyeX + eyeW / 2), int(eyeY + eyeH / 2)),
                        3, (0, 255, 0), 1)
            toSleep = currentTime - lastReadTime
            lastReadTime = currentTime
            if toSleep < self.interval:
                sleep(toSleep)
            if not self.showWindow:
                continue
            self.windowFrameQueue.put(('FaceAndEyeDetection', frame))
        self.sensor.release()
