import cv2

from datatype import ApplicationUserSide


class FaceDetection(ApplicationUserSide):

    def __init__(self, appID: int):
        super().__init__(appID)
        self.face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')

    def process(self, inputData):
        frame = inputData
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        return frame


class FaceAndEyeDetection(ApplicationUserSide):

    def __init__(self, appID: int):
        super().__init__(appID)
        self.face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')
        self.eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

    def process(self, inputData):
        frame = inputData
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            for (x, y, w, h) in eyes:
                cv2.rectangle(roi_color, (x, y),
                              (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(roi_color, (int(x + w / 2), int(y + h / 2)),
                           3, (0, 255, 0), 1)
        return frame


class ColorTracking(ApplicationUserSide):

    def __init__(self, appID: int):
        super().__init__(appID)
        self.face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')
        self.eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

    def process(self, inputData):
        frame = inputData
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            for (x, y, w, h) in eyes:
                cv2.rectangle(roi_color, (x, y),
                              (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(roi_color, (int(x + w / 2), int(y + h / 2)),
                           3, (0, 255, 0), 1)
        return frame


appList = [FaceDetection(0), FaceAndEyeDetection(1)]
