import cv2
import os
import threading
import numpy as np
from datatype import ApplicationUserSide
from queue import Queue


class FaceDetection(ApplicationUserSide):

    def run(self):
        self.appName = 'FaceDetection'
        self.broker.run(
            label='%s-%d' % (self.appName, self.targetWidth),
            mode='sequential'
        )

        threading.Thread(target=self.__sendData).start()
        threading.Thread(target=self.__receiveResult).start()
        threading.Thread(target=self.__handleResult).start()

    def __sendData(self):
        self.dataIDSubmittedQueue = Queue(1)
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            dataID = self.createDataFrame(frame)
            self.broker.submit(
                data=frame,
                dataID=dataID,
                mode='sequential',
                label='%d' % self.targetWidth
            )
            self.dataIDSubmittedQueue.put(dataID)

        self.capture.release()

    def __receiveResult(self):
        while True:
            message = self.broker.resultQueue.get()
            self.result[message['dataID']].put(message['result'])

    def __handleResult(self):
        while True:
            dataID = self.dataIDSubmittedQueue.get()
            faces = self.result[dataID].get()
            frame = self.data[dataID]
            for (x, y, w, h, roi_gray) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            cv2.imshow("App-%d %s" % (self.appID, self.appName), frame)
            del self.data[dataID]

            if cv2.waitKey(1) == ord('q'):
                break


class FaceAndEyeDetection(ApplicationUserSide):
    def run(self):
        self.appName = 'FaceAndEyeDetection'
        self.broker.run(
            label='%s-%d' % (self.appName, self.targetWidth),
            mode='sequential'
        )

        threading.Thread(target=self.__sendData).start()
        threading.Thread(target=self.__receiveResult).start()
        threading.Thread(target=self.__handleResult).start()

    def __sendData(self):
        self.dataIDSubmittedQueue = Queue(1)
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            dataID = self.createDataFrame(frame)
            self.broker.submit(
                data=frame,
                dataID=dataID,
                mode='sequential',
                label='%d' % self.targetWidth
            )
            self.dataIDSubmittedQueue.put(dataID)

        self.capture.release()

    def __receiveResult(self):
        while True:
            message = self.broker.resultQueue.get()
            self.result[message['dataID']].put(message['result'])

    def __handleResult(self):
        while True:
            dataID = self.dataIDSubmittedQueue.get()
            faces = self.result[dataID].get()
            frame = self.data[dataID]
            for (x, y, w, h, eyes) in faces:
                roi_color = frame[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                for (x, y, w, h) in eyes:
                    cv2.rectangle(roi_color, (x, y),
                                  (x + w, y + h), (0, 0, 255), 2)
                    cv2.circle(roi_color, (int(x + w / 2), int(y + h / 2)),
                               3, (0, 255, 0), 1)
            cv2.imshow("App-%d %s" % (self.appID, self.appName), frame)
            del self.data[dataID]
            if cv2.waitKey(1) == ord('q'):
                break


class ColorTracking(ApplicationUserSide):

    @staticmethod
    def nothing():
        pass

    def __receiveResult(self):
        while True:
            message = self.broker.resultQueue.get()
            self.result[message['dataID']].put(message['result'])

    def run(self):
        self.appName = 'ColorTracking'
        self.broker.run(
            label='%s-%d' % (self.appName, self.targetWidth),
            mode='sequential'
        )
        threading.Thread(target=self.__receiveResult).start()

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
        targetWidth = 640
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break

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

            frame = self.resizeFrame(frame)
            inputData = (frame,
                         hueLow, hueUp,
                         hue2Low, hue2Up,
                         Ls, Us,
                         Lv, Uv,
                         l_b, u_b,
                         l_b2, u_b2
                         )
            dataID = self.createDataFrame(inputData)
            self.broker.submit(
                inputData,
                dataID,
                mode='sequential',
                label='%d' % self.targetWidth
            )
            resultData = self.result[dataID].get()
            (FGmaskComp, frame) = resultData

            cv2.imshow('FGmaskComp', FGmaskComp)
            cv2.moveWindow('FGmaskComp', 0, 530)

            cv2.imshow('nanoCam', frame)
            cv2.moveWindow('nanoCam', 0, 0)

            if cv2.waitKey(1) == ord('q'):
                break
        self.capture.release()
        cv2.destroyAllWindows()


class VideoOCR(ApplicationUserSide):

    def __preprocess(self, q: Queue):
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            q.put(frame)
        q.put(None)

    def run(self):
        self.appName = 'VideoOCR'
        self.broker.run(
            label='%s-%d' % (self.appName, self.targetWidth),
            mode='sequential'
        )
        framesQueue = Queue()
        threading.Thread(
            target=self.__preprocess,
            args=(framesQueue,)
        ).start()
        print("[*] Sending frames ...")
        while True:
            frame = framesQueue.get()
            if frame is None:
                break
            inputData = (frame, False)
            self.broker.submit(
                inputData,
                dataID=-1,
                mode='sequential',
                label='%d' % self.targetWidth
            )
        print("[*] Sent all the frames and waiting for result ...")
        inputData = (None, True)
        self.broker.submit(
            inputData,
            dataID=-1,
            mode='sequential',
            label='%d' % self.targetWidth
        )

        result = self.broker.resultQueue.get()

        print(result['result'], '\r\n [*] The text is at above.')
        os._exit(0)
