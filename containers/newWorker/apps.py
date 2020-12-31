import cv2

from datatype import ApplicationUserSide


class TestApp(ApplicationUserSide):
    def __init__(self, appID: int):
        super().__init__(appID, 'TestApp')

    def process(self, inputData):
        return inputData * 2


class FaceDetection(ApplicationUserSide):

    def __init__(self, appID: int):
        super().__init__(appID, 'FaceDetection')
        self.face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')

    def process(self, inputData):
        frame = inputData
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        result = []
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            result.append((x, y, w, h, roi_gray))
        return result


class EyeDetection(ApplicationUserSide):

    def __init__(self, appID: int):
        super().__init__(appID, 'EyeDetection')
        self.eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

    def process(self, inputData):
        faces = inputData
        for i, (x, y, w, h, roi_gray) in enumerate(faces):
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            faces[i] = (x, y, w, h, eyes)
        return faces


class ColorTracking(ApplicationUserSide):

    def process(self, inputData):

        (frame,
         hueLow, hueUp,
         hue2Low, hue2Up,
         Ls, Us,
         Lv, Uv,
         l_b, u_b,
         l_b2, u_b2
         ) = inputData
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        FGmask = cv2.inRange(hsv, l_b, u_b)
        FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
        FGmaskComp = cv2.add(FGmask, FGmask2)

        contours, _ = cv2.findContours(
            FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            (x, y, w, h) = cv2.boundingRect(cnt)
            if area >= 50:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)

        return FGmaskComp, frame
