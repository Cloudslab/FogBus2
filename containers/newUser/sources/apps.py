import cv2
import threading
import numpy as np
from abc import abstractmethod
from queue import Queue
from random import randint
from connection import Median
from time import time


class ApplicationUserSide:

    def __init__(
            self,
            appName: str,
            videoPath: str = None,
            targetHeight: int = 640,
            showWindow: bool = True):
        self.appName = appName
        if appName in {
            'FaceDetection',
            'FaceAndEyeDetection',
            'ColorTracking',
            'VideoOCR'
        }:
            self.capture = cv2.VideoCapture(0) if videoPath is None \
                else cv2.VideoCapture(videoPath)
        else:
            self.capture = None
        self.result: Queue = Queue()
        self.dataToSubmit: Queue = Queue()
        self.targetHeight = targetHeight
        self.showWindow: bool = showWindow
        self.videoPath: str = videoPath
        self.respondTime: Median = Median(maxRecordNumber=32)
        self.respondTimeCount = 0

    def resizeFrame(self, frame):
        width = frame.shape[1]
        height = frame.shape[0]
        resizedWidth = int(width * self.targetHeight / height)
        return cv2.resize(frame, (resizedWidth, self.targetHeight))

    def run(self):
        threading.Thread(target=self._run).start()

    @staticmethod
    def _run():
        raise NotImplementedError


class FaceDetection(ApplicationUserSide):

    def __init__(
            self,
            appName: str,
            videoPath: str,
            targetHeight: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow)

    def _run(self):
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            self.dataToSubmit.put(frame)
            lastDataSentTime = time()
            faces = self.result.get()
            respondTime = (time() - lastDataSentTime) * 1000
            self.respondTime.update(respondTime)
            self.respondTimeCount += 1
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
            targetHeight: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow)

    def _run(self):
        self.dataIDSubmittedQueue = Queue(1)
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = self.resizeFrame(frame)
            self.dataToSubmit.put(frame)
            lastDataSentTime = time()
            faces = self.result.get()
            respondTime = (time() - lastDataSentTime) * 1000
            self.respondTime.update(respondTime)
            self.respondTimeCount += 1
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
            targetHeight: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetHeight=targetHeight,
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
            lastDataSentTime = time()
            resultData = self.result.get()
            respondTime = (time() - lastDataSentTime) * 1000
            self.respondTime.update(respondTime)
            self.respondTimeCount += 1
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
            targetHeight: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetHeight=targetHeight,
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

        lastDataSentTime = time()
        result = self.result.get()
        respondTime = (time() - lastDataSentTime) * 1000
        self.respondTime.update(respondTime)
        self.respondTimeCount += 1
        print(result, '\r\n [*] The text is at above.')


class GameOfLifeSerialised(ApplicationUserSide):

    def __init__(
            self,
            appName: str,
            videoPath: str,
            targetHeight: int,
            showWindow: bool):
        super().__init__(
            appName=appName,
            videoPath=videoPath,
            targetHeight=targetHeight,
            showWindow=showWindow)
        t = self.targetHeight // 128 * 128

        self._resizeFactor = 4
        self.height = t // self._resizeFactor
        self.width = t * 2 // self._resizeFactor
        self.generationNumber = None
        self.world = np.zeros((self.height, self.width, 1), np.uint8)
        self.newStates = set([])
        self.frameUpdateGap = 1 / 60
        self.mayChange = set([])

    def _run(self):
        self.startWithText()
        gen = 0
        while True:
            gen += 1
            if self._resizeFactor != 1:
                showWorld = cv2.resize(
                    self.world,
                    (self.width * self._resizeFactor,
                     self.height * self._resizeFactor),
                    interpolation=cv2.INTER_AREA)
            else:
                showWorld = self.world

            if self.showWindow:
                cv2.imshow(
                    self.appName,
                    showWorld)
                # cv2.waitKey(0)
                if cv2.waitKey(1) == ord('q'):
                    break
            print('\r[*] Generation %d' % gen, end='')
            inputData = (
                self.world,
                self.height,
                self.width,
                self.mayChange,
                set([]),
                set([]))
            self.dataToSubmit.put(inputData)
            lastDataSentTime = time()
            result = self.result.get()
            respondTime = (time() - lastDataSentTime) * 1000
            self.respondTime.update(respondTime)
            self.respondTimeCount += 1
            self.newStates.update(result[4])
            self.mayChange.update(result[5])
            self.changeStates()

        print('[*] Bye')

    def startWithText(self):
        text = 'Qifan Deng'
        color = (255, 0, 0)
        textSize = cv2.getTextSize(text, 0, 1, 2)[0]
        positionX = (self.world.shape[1] - textSize[0]) // 2
        positionY = (self.world.shape[0] + textSize[1]) // 2
        world = cv2.putText(
            self.world,
            text,
            (positionX, positionY),
            0,
            1,
            color,
            1,
            cv2.LINE_AA)
        _, self.world = cv2.threshold(world, 127, 255, cv2.THRESH_BINARY)
        self.initMayChange(theWholeWorld=True)
        if self.showWindow:
            cv2.imshow(
                self.appName,
                cv2.resize(
                    self.world,
                    (self.width * self._resizeFactor,
                     self.height * self._resizeFactor),
                    interpolation=cv2.INTER_AREA))
            print('[*] This is your initial world. Press \'Space\' to start.')
            cv2.waitKey(0)

    def initMayChange(self, theWholeWorld=False):
        self.mayChange = set([])
        for i in range(0, self.height):
            for j in range(0, self.width):
                if theWholeWorld:
                    self.mayChange.update([(i, j)])
                    continue
                if not self.doesChange(i, j):
                    continue
                neighbours = self.affectedNeighbours(i, j)
                self.mayChange.update(neighbours)

    def doesChange(self, i, j) -> bool:
        count = self.neighboursCount(i, j)
        if count == 2:
            return False
        if count == 3:
            return not self.world[i][j] == 255
        return not self.world[i][j] == 0

    def neighboursCount(self, i, j):
        count = 0
        neighbours = self.getNeighbours(i, j)
        for i, j in neighbours:
            count += 1 if self.world[i][j] else 0
        return count

    def getNeighbours(self, i, j):
        neighbours = [
            (i - 1, j - 1),
            (i - 1, j),
            (i - 1, (j + 1) % self.width),
            (i, j - 1),
            (i, (j + 1) % self.width),
            ((i + 1) % self.height, j - 1),
            ((i + 1) % self.height, j),
            ((i + 1) % self.height, (j + 1) % self.width)]
        return neighbours

    def affectedNeighbours(self, i, j):
        neighbours = set([])
        wide = 2
        for iNeighbour in range(i - wide, i + wide):
            for jNeighbour in range(j - wide, j + wide):
                neighbours.update([(iNeighbour % self.height, jNeighbour % self.width)])
        return neighbours

    def changeStates(self):
        for i, j in self.newStates:
            if self.world[i][j] == 0:
                self.world[i][j] = 255
                continue
            self.world[i][j] = 0
        self.newStates = set([])


class GameOfLifeParallelized(GameOfLifeSerialised):

    def _run(self):
        self.appName = 'GameOfLifeParallelized'
        self.startWithText()
        gen = 0
        while True:
            gen += 1
            if self._resizeFactor != 1:
                showWorld = cv2.resize(
                    self.world,
                    (self.width * self._resizeFactor,
                     self.height * self._resizeFactor),
                    interpolation=cv2.INTER_AREA)
            else:
                showWorld = self.world

            if self.showWindow:
                cv2.imshow(
                    self.appName,
                    showWorld)
                # cv2.waitKey(0)
                if cv2.waitKey(1) == ord('q'):
                    break
            print('\r[*] Generation %d' % gen, end='')
            inputData = (
                self.world,
                self.height,
                self.width,
                self.mayChange,
                set([]),
                set([]))
            self.dataToSubmit.put(inputData)
            lastDataSentTime = time()
            resCount = 0
            self.newStates = set([])
            self.mayChange = set([])
            while resCount < 62:
                result = self.result.get()
                resCount += 1
                self.newStates.update(result[4])
                self.mayChange.update(result[5])
            respondTime = (time() - lastDataSentTime) * 1000
            self.respondTime.update(respondTime)
            self.respondTimeCount += 1
            self.changeStates()

        print('[*] Bye')


class GameOfLifePyramid(GameOfLifeSerialised):

    def _run(self):
        self.appName = 'GameOfLifePyramid'
        self.startWithText()
        gen = 0
        while True:
            gen += 1
            if self._resizeFactor != 1:
                showWorld = cv2.resize(
                    self.world,
                    (self.width * self._resizeFactor,
                     self.height * self._resizeFactor),
                    interpolation=cv2.INTER_AREA)
            else:
                showWorld = self.world

            if self.showWindow:
                cv2.imshow(
                    self.appName,
                    showWorld)
                # cv2.waitKey(0)
                if cv2.waitKey(1) == ord('q'):
                    break
            print('\r[*] Generation %d' % gen, end='')
            inputData = (
                self.world,
                self.height,
                self.width,
                self.mayChange,
                set([]),
                set([]))
            self.dataToSubmit.put(inputData)
            lastDataSentTime = time()
            resCount = 0
            self.newStates = set([])
            self.mayChange = set([])
            while resCount < 32:
                result = self.result.get()
                resCount += 1
                self.newStates.update(result[4])
                self.mayChange.update(result[5])
            respondTime = (time() - lastDataSentTime) * 1000
            self.respondTime.update(respondTime)
            self.respondTimeCount += 1
            self.changeStates()

        print('[*] Bye')
