import cv2
import numpy as np
from datatype import ApplicationUserSide
from broker import Broker


class FaceDetection(ApplicationUserSide):

    def run(self):
        self.appName = 'FaceDetection'
        self.broker.run()

        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            width = frame.shape[1]
            height = frame.shape[0]
            targetWidth = int(width * 640 / height)
            frame = cv2.resize(frame, (targetWidth, 640))
            resultFrame = self.broker.submit(self.appID, frame)
            while resultFrame is None:
                resultFrame = self.broker.submit(self.appID, frame)
            cv2.imshow("App-%d %s" % (self.appID, self.appName), resultFrame)
            if cv2.waitKey(1) == ord('q'):
                break
        self.capture.release()


class FaceAndEyeDetection(ApplicationUserSide):
    def run(self):
        self.broker.run()

        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            width = frame.shape[1]
            height = frame.shape[0]
            targetWidth = int(width * 640 / height)
            frame = cv2.resize(frame, (targetWidth, 640))
            resultFrame = self.broker.submit(self.appID, frame)
            while resultFrame is None:
                resultFrame = self.broker.submit(self.appID, frame)
            cv2.imshow("App-%d %s" % (self.appID, self.appName), resultFrame)
            if cv2.waitKey(1) == ord('q'):
                break
        self.capture.release()


class ColorTracking(ApplicationUserSide):
    # WIP

    def __init__(self, appID: int, appName: str, broker: Broker, videoPath=None):
        super().__init__(appID, appName, broker, videoPath)
        self.face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')
        self.eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

    def nothing():
        pass

    def run(self):
        cv2.namedWindow('Trackbars')
        cv2.moveWindow('Trackbars', 1320, 0)

        cv2.createTrackbar('hueLower', 'Trackbars', 50, 179, self.nothing)
        cv2.createTrackbar('hueUpper', 'Trackbars', 100, 179, self.nothing)

        cv2.createTrackbar('hue2Lower', 'Trackbars', 50, 179, self.nothing)
        cv2.createTrackbar('hue2Upper', 'Trackbars', 100, 179, self.nothing)

        cv2.createTrackbar('satLow', 'Trackbars', 100, 255, self.nothing)
        cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, self.nothing)
        cv2.createTrackbar('valLow', 'Trackbars', 100, 255, self.nothing)
        cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, self.nothing)
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
            hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')

            hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
            hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')

            Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
            Us = cv2.getTrackbarPos('satHigh', 'Trackbars')

            Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
            Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')

            l_b = np.array([hueLow, Ls, Lv])
            u_b = np.array([hueUp, Us, Uv])

            l_b2 = np.array([hue2Low, Ls, Lv])
            u_b2 = np.array([hue2Up, Us, Uv])

            FGmask = cv2.inRange(hsv, l_b, u_b)
            FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
            FGmaskComp = cv2.add(FGmask, FGmask2)
            cv2.imshow('FGmaskComp', FGmaskComp)
            cv2.moveWindow('FGmaskComp', 0, 530)

            contours, _ = cv2.findContours(
                FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                (x, y, w, h) = cv2.boundingRect(cnt)
                if area >= 50:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)

            cv2.imshow('nanoCam', frame)
            cv2.moveWindow('nanoCam', 0, 0)

            if cv2.waitKey(1) == ord('q'):
                break
        self.capture.release()
        cv2.destroyAllWindows()
