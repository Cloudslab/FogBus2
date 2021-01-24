import cv2
import threading
import numpy as np
from abc import abstractmethod
from queue import Queue
from random import randint


class ApplicationUserSide:

    def __init__(
            self,
            appName: str,
            videoPath: str = None,
            targetWidth: int = 640,
            showWindow: bool = True):
        self.appName = appName
        self.capture = cv2.VideoCapture(0) if videoPath is None \
            else cv2.VideoCapture(videoPath)
        self.result: Queue = Queue()
        self.dataToSubmit: Queue = Queue()
        self.targetWidth = targetWidth
        self.showWindow: bool = showWindow
        self.videoPath: str = videoPath

    def resizeFrame(self, frame):
        width = frame.shape[1]
        height = frame.shape[0]
        resizedWidth = int(width * self.targetWidth / height)
        return cv2.resize(frame, (resizedWidth, self.targetWidth))

    def _runApp(self):
        threading.Thread(target=self._run).start()

    @staticmethod
    def _run():
        raise NotImplementedError


class FaceDetection(ApplicationUserSide):

    def __init__(
            self,
            appName: str,
            videoPath: str,
            targetWidth: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetWidth=targetWidth,
            showWindow=showWindow)

    def _run(self):
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            self.dataToSubmit.put(frame)

            faces = self.result.get()
            for (x, y, w, h, roi_gray) in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (255, 0, 0),
                    2)
            if self.showWindow:
                cv2.imshow(self.appName, frame)
                if cv2.waitKey(1) == ord('q'):
                    break
        self.capture.release()


class FaceAndEyeDetection(ApplicationUserSide):

    def __init__(
            self,
            appName: str,
            videoPath: str,
            targetWidth: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetWidth=targetWidth,
            showWindow=showWindow)

    def _run(self):
        self.dataIDSubmittedQueue = Queue(1)
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            self.dataToSubmit.put(frame)

            faces = self.result.get()
            for (x, y, w, h, eyes) in faces:
                roi_color = frame[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                for (x, y, w, h) in eyes:
                    cv2.rectangle(roi_color, (x, y),
                                  (x + w, y + h), (0, 0, 255), 2)
                    cv2.circle(roi_color, (int(x + w / 2), int(y + h / 2)),
                               3, (0, 255, 0), 1)

            if self.showWindow:
                cv2.imshow(self.appName, frame)
                if cv2.waitKey(1) == ord('q'):
                    break
        self.capture.release()


class ColorTracking(ApplicationUserSide):

    def __init__(
            self,
            appName: str,
            videoPath: str,
            targetWidth: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetWidth=targetWidth,
            showWindow=showWindow)

    @staticmethod
    def nothing(arg):
        pass

    def _run(self):

        if self.showWindow:
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
                         l_b2, u_b2
                         )
            self.dataToSubmit.put(inputData)
            resultData = self.result.get()
            (FGmaskComp, frame) = resultData

            if self.showWindow:
                cv2.imshow('FGmaskComp', FGmaskComp)
                cv2.moveWindow('FGmaskComp', 0, 530)

                cv2.imshow('nanoCam', frame)
                cv2.moveWindow('nanoCam', 0, 0)

                if cv2.waitKey(1) == ord('q'):
                    break
        self.capture.release()
        cv2.destroyAllWindows()


class VideoOCR(ApplicationUserSide):

    def __init__(
            self,
            appName: str,
            videoPath: str,
            targetWidth: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetWidth=targetWidth,
            showWindow=showWindow)

    def __preprocess(self, q: Queue):
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            q.put(frame)
        q.put(None)

    def _run(self):
        print("[*] Sending frames ...")
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            inputData = (frame, False)
            self.dataToSubmit.put(inputData)
        inputData = (None, True)
        self.dataToSubmit.put(inputData)
        print("[*] Sent all the frames and waiting for result ...")

        result = self.result.get()
        print(result, '\r\n [*] The text is at above.')
