import cv2

from .base import BaseTask


class ColorTracking(BaseTask):
    def __init__(self):
        super().__init__(taskID=3, taskName='ColorTracking')

    def exec(self, inputData):
        (frame,
         hueLow, hueUp,
         hue2Low, hue2Up,
         Ls, Us,
         Lv, Uv,
         l_b, u_b,
         l_b2, u_b2) = inputData
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        FGmask = cv2.inRange(hsv, l_b, u_b)
        FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
        FGmaskComp = cv2.add(FGmask, FGmask2)

        contours, _ = cv2.findContours(
            FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda x_: cv2.contourArea(x_),
                          reverse=True)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            (x, y, w, h) = cv2.boundingRect(cnt)
            if area >= 50:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)

        return FGmaskComp, frame
