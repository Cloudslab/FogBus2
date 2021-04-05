from queue import Queue
from time import time

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


class VideoOCR(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent):
        super().__init__(
            appName='VideoOCR',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent)

    def prepare(self):
        self.canStart.wait()

    def __preprocess(self, q: Queue):
        while True:
            ret, frame = self.sensor.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            q.put(frame)
        q.put(None)

    def _run(self):
        self.basicComponent.debugLogger.info("[*] Sending frames ...")
        while True:
            ret, frame = self.sensor.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            inputData = (frame, False)
            self.dataToSubmit.put(inputData)
        inputData = (None, True)
        self.dataToSubmit.put(inputData)
        self.basicComponent.debugLogger.info(
            "[*] Sent all the frames and waiting for result ...")

        lastDataSentTime = time()
        result = self.resultForActuator.get()
        responseTime = (time() - lastDataSentTime) * 1000
        self.responseTime.update(responseTime)
        self.responseTimeCount += 1
        self.basicComponent.debugLogger.info(
            '%s%s%s',
            'The text is as below, \n%s\n' % ('=' * 42),
            result,
            '\n%s\nThe text is at above.' % ('=' * 42))
