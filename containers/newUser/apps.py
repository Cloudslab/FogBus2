import cv2
import threading
import numpy as np
from datatype import ApplicationUserSide


class FaceDetection(ApplicationUserSide):

    # this is method
    def run(self):
        self.appName = 'FaceDetection'
        self.broker.run()

        threading.Thread(target=self.__sendData).start()
        threading.Thread(target=self.__receiveResult).start()
        threading.Thread(target=self.__handleResult).start()

    def __sendData(self):

        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            if self.dataIDSubmittedQueue.qsize() > 10:
                continue
            width = frame.shape[1]
            height = frame.shape[0]
            targetWidth = int(width * 640 / height)
            frame = cv2.resize(frame, (targetWidth, 640))
            dataID, data = self.createDataFrame(frame)
            self.broker.submit(self.appID, data=data, dataID=dataID)
            # result = self.result[dataID].get()
            # del self.data[dataID]
            # cv2.imshow("App-%d %s" % (self.appID, self.appName), result)
            # if cv2.waitKey(1) == ord('q'):
            #     break
            self.dataIDSubmittedQueue.put(dataID)

        self.capture.release()

    def __receiveResult(self):
        while True:
            message = self.broker.resultQueue.get()
            self.result[message['dataID']].put(message['result'])

    def __handleResult(self):
        while True:
            dataID = self.dataIDSubmittedQueue.get()
            result = self.result[dataID].get()
            del self.data[dataID]
            cv2.imshow("App-%d %s" % (self.appID, self.appName), result)
            if cv2.waitKey(1) == ord('q'):
                break


class FaceAndEyeDetection(ApplicationUserSide):
    def run(self):
        self.appName = 'FaceAndEyeDetection'
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

    @staticmethod
    def nothing():
        pass

    def run(self):
        self.appName = 'ColorTracking'
        cv2.namedWindow('Trackbars')

        self.broker.run()
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

            width = frame.shape[1]
            height = frame.shape[0]
            targetWidth = int(width * 320 / height)
            frame = cv2.resize(frame, (targetWidth, 320))
            inputData = (frame,
                         hueLow, hueUp,
                         hue2Low, hue2Up,
                         Ls, Us,
                         Lv, Uv,
                         l_b, u_b,
                         l_b2, u_b2
                         )

            resultData = self.broker.submit(self.appID, inputData)
            (FGmaskComp, frame) = resultData

            cv2.imshow('FGmaskComp', FGmaskComp)
            cv2.moveWindow('FGmaskComp', 0, 530)

            cv2.imshow('nanoCam', frame)
            cv2.moveWindow('nanoCam', 0, 0)

            if cv2.waitKey(1) == ord('q'):
                break
        self.capture.release()
        cv2.destroyAllWindows()
