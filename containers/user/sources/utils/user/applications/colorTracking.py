from random import randint
from time import time

import cv2
import numpy as np

from .base import ApplicationUserSide
from ...component.basic import BasicComponent


def _empty(*args):
    return


class ColorTracking(ApplicationUserSide):

    def __init__(
            self,
            videoPath: str,
            targetHeight: int,
            showWindow: bool,
            basicComponent: BasicComponent):
        super().__init__(
            appName='ColorTracking',
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow,
            basicComponent=basicComponent)

    def prepare(self):
        if self.showWindow:
            cv2.namedWindow('Trackbars')
            cv2.moveWindow('Trackbars', 1320, 0)

            cv2.createTrackbar('hueLower', 'Trackbars', 50, 179, _empty)
            cv2.createTrackbar('hueUpper', 'Trackbars', 100, 179, _empty)

            cv2.createTrackbar('hue2Lower', 'Trackbars', 50, 179, _empty)
            cv2.createTrackbar('hue2Upper', 'Trackbars', 100, 179, _empty)

            cv2.createTrackbar('satLow', 'Trackbars', 100, 255, _empty)
            cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, _empty)
            cv2.createTrackbar('valLow', 'Trackbars', 100, 255, _empty)
            cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, _empty)

    def _run(self):
        self.basicComponent.debugLogger.info(
            'Application is running: %s', self.appName)
        while True:
            ret, frame = self.sensor.read()
            if not ret:
                break

            if self.showWindow:
                hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
                hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')
                hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
                hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')
                Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
                Us = cv2.getTrackbarPos('satHigh', 'Trackbars')
                Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
                Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')
            else:
                hueLow = randint(0, 179)
                hueUp = randint(0, 179)
                hue2Low = randint(0, 179)
                hue2Up = randint(0, 179)
                Ls = randint(0, 255)
                Us = randint(0, 255)
                Lv = randint(0, 255)
                Uv = randint(0, 255)

            l_b = np.array([hueLow, Ls, Lv])
            u_b = np.array([hueUp, Us, Uv])

            l_b2 = np.array([hue2Low, Ls, Lv])
            u_b2 = np.array([hue2Up, Us, Uv])

            frame = self.resizeFrame(frame)
            inputData = (frame,
                         hueLow, hueUp,
                         hue2Low, hue2Up,
                         Ls, Us,
                         Lv, Uv,
                         l_b, u_b,
                         l_b2, u_b2)
            self.dataToSubmit.put(inputData)
            lastDataSentTime = time()
            resultData = self.resultForActuator.get()
            responseTime = (time() - lastDataSentTime) * 1000
            self.responseTime.update(responseTime)
            self.responseTimeCount += 1
            (FGmaskComp, frame) = resultData

            if not self.showWindow:
                return
            self.windowFrameQueue.put(('FGmaskComp', FGmaskComp))
            self.windowFrameQueue.put(('nanoCam', frame))
        self.sensor.release()
