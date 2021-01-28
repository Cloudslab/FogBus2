import cv2
import pytesseract
import editdistance
import numpy as np
from abc import abstractmethod


class TasksWorkerSide:

    def __init__(self, taskID: int, taskName: str):
        self.taskID = taskID
        self.taskName = taskName
        self.taskCalls = 0
        self.processedTime = 0
        self.processedCount = 0

    @abstractmethod
    def process(self, inputData):
        pass


class TestApp(TasksWorkerSide):
    def __init__(self, appID: int):
        super().__init__(appID, 'TestApp')

    def process(self, inputData):
        return inputData * 2


class FaceDetection(TasksWorkerSide):

    def __init__(self):
        super().__init__(taskID=1, taskName='FaceDetection')
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


class EyeDetection(TasksWorkerSide):

    def __init__(self):
        super().__init__(taskID=2, taskName='EyeDetection')
        self.eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

    def process(self, inputData):
        faces = inputData
        for i, (x, y, w, h, roi_gray) in enumerate(faces):
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            faces[i] = (x, y, w, h, eyes)
        return faces


class ColorTracking(TasksWorkerSide):
    def __init__(self):
        super().__init__(taskID=3, taskName='ColorTracking')

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
        contours = sorted(contours, key=lambda x_: cv2.contourArea(x_), reverse=True)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            (x, y, w, h) = cv2.boundingRect(cnt)
            if area >= 50:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)

        return FGmaskComp, frame


class BlurAndPHash(TasksWorkerSide):
    def __init__(self):
        super().__init__(taskID=4, taskName='BlurAndPHash')
        self.thresholdLaplacian = 120
        self.thresholdDiffStop = 120
        self.thresholdDiffPre = 25
        self.hashLen = 32
        self.preStopPHash = None
        self.prePHash = None
        self.n = 0

    def process(self, inputData):
        frame, isLastFrame = inputData
        if isLastFrame:
            return None, isLastFrame

        currPHash = self.getPHash(frame)
        if currPHash is None:
            return None

        if self.preStopPHash is None:
            self.preStopPHash = currPHash
            self.prePHash = currPHash
            return None

        diffStop = self.hamDistance(self.preStopPHash, currPHash)
        diffPre = self.hamDistance(self.prePHash, currPHash)
        self.prePHash = currPHash

        if diffStop >= self.thresholdDiffStop \
                or diffPre <= self.thresholdDiffPre:
            return None

        self.n += 1
        if self.n <= 3:
            return None
        self.n = 0
        self.preStopPHash = currPHash
        return frame, isLastFrame

    def getPHash(self, img):
        pHash = None
        laplacian = cv2.Laplacian(img, cv2.CV_64F).var()
        if laplacian <= self.thresholdLaplacian:
            return pHash
        imgGray = cv2.resize(
            cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
            (self.hashLen, self.hashLen),
            cv2.INTER_AREA)
        height, width = imgGray.shape[:2]
        matrixOriginal = np.zeros(
            (height, width),
            np.float32)
        matrixOriginal[:height, :width] = imgGray

        matrix = cv2.dct(cv2.dct(matrixOriginal))
        matrix.resize(self.hashLen, self.hashLen)
        matrixFlatten = matrix.flatten()

        averageValue = sum(matrixFlatten) * 1. / len(matrixFlatten)
        pHash = 0
        for i in matrixFlatten:
            pHash <<= 1
            if i >= averageValue:
                pHash += 1
        return pHash

    @staticmethod
    def hamDistance(x, y):
        tmp = x ^ y
        distance = 0

        while tmp > 0:
            distance += tmp & 1
            tmp >>= 1

        return distance


class OCR(TasksWorkerSide):
    def __init__(self):
        super().__init__(taskID=5, taskName='OCR')
        self.text = ''
        self.preText = None
        self.thresholdEditDistance = 800

    def process(self, inputData):
        (frame, isLastFrame) = inputData
        if isLastFrame:
            return self.text
        currText = pytesseract.image_to_string(frame)
        if self.preText is None:
            self.text = currText
            self.preText = currText
            return None
        editDistance = self.editDistance(self.preText, currText)
        if editDistance <= self.thresholdEditDistance:
            return None
        self.text += currText
        self.preText = currText
        return None

    @staticmethod
    def editDistance(textA, textB):
        return editdistance.eval(textA, textB)


class GameOfLife(TasksWorkerSide):
    def __init__(
            self,
            taskID: int,
            taskName: str,
            focusArea):
        super().__init__(taskID=taskID, taskName=taskName)
        self.world = None
        self.height = None
        self.width = None
        self.focusArea = focusArea

    def adjustFocusArea(self):

        focusArea = [list(point) for point in self.focusArea]
        for i in range(2):
            for j in range(2):
                focusArea[i][j] *= self.height // 128
        self.focusArea = focusArea

    def process(self, inputData):
        self.world = inputData[0]
        self.height = inputData[1]
        self.width = inputData[2]
        self.adjustFocusArea()
        mayChange = inputData[3]
        newStates = inputData[4]
        mayChangeInNextRound = inputData[5]
        for i, j in mayChange:
            if not self.hitMyFocus(i, j):
                continue
            if self.doesChange(i, j):
                newStates.update([(i, j)])
                neighbours = self.affectedNeighbours(i, j)
                mayChangeInNextRound.update(neighbours)

        return self.world, self.height, self.width, mayChange, newStates, mayChangeInNextRound

    def hitMyFocus(self, i, j) -> bool:
        if i < self.focusArea[0][0]:
            return False
        if i > self.focusArea[1][0]:
            return False
        if j < self.focusArea[0][1]:
            return False
        if j > self.focusArea[1][1]:
            return False
        return True

    def affectedNeighbours(self, i, j):
        neighbours = set([])
        wide = 2
        for iNeighbour in range(i - wide, i + wide):
            for jNeighbour in range(j - wide, j + wide):
                neighbours.update([(iNeighbour % self.height, jNeighbour % self.width)])
        return neighbours

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


class GameOfLife0(GameOfLife):
    def __init__(self):
        super().__init__(
            42,
            'GameOfLife0',
            ((0, 0), (64, 128)))


class GameOfLife1(GameOfLife):
    def __init__(self):
        super().__init__(
            43,
            'GameOfLife1',
            ((0, 128), (64, 256)))


class GameOfLife2(GameOfLife):
    def __init__(self):
        super().__init__(
            44,
            'GameOfLife2',
            ((64, 128), (96, 192)))


class GameOfLife3(GameOfLife):
    def __init__(self):
        super().__init__(
            45,
            'GameOfLife3',
            ((64, 192), (96, 256)))


class GameOfLife4(GameOfLife):
    def __init__(self):
        super().__init__(
            46,
            'GameOfLife4',
            ((96, 192), (112, 224)))


class GameOfLife5(GameOfLife):
    def __init__(self):
        super().__init__(
            47,
            'GameOfLife5',
            ((96, 224), (112, 256)))


class GameOfLife6(GameOfLife):
    def __init__(self):
        super().__init__(
            48,
            'GameOfLife6',
            ((112, 224), (120, 240)))


class GameOfLife7(GameOfLife):
    def __init__(self):
        super().__init__(
            49,
            'GameOfLife7',
            ((112, 240), (120, 256)))


class GameOfLife8(GameOfLife):
    def __init__(self):
        super().__init__(
            50,
            'GameOfLife8',
            ((120, 240), (128, 248)))


class GameOfLife9(GameOfLife):
    def __init__(self):
        super().__init__(
            51,
            'GameOfLife9',
            ((120, 248), (128, 256)))


class GameOfLife10(GameOfLife):
    def __init__(self):
        super().__init__(
            52,
            'GameOfLife10',
            ((120, 224), (128, 232)))


class GameOfLife11(GameOfLife):
    def __init__(self):
        super().__init__(
            53,
            'GameOfLife11',
            ((120, 232), (128, 240)))


class GameOfLife12(GameOfLife):
    def __init__(self):
        super().__init__(
            54,
            'GameOfLife12',
            ((112, 192), (120, 208)))


class GameOfLife13(GameOfLife):
    def __init__(self):
        super().__init__(
            55,
            'GameOfLife13',
            ((112, 208), (120, 224)))


class GameOfLife14(GameOfLife):
    def __init__(self):
        super().__init__(
            56,
            'GameOfLife14',
            ((120, 208), (128, 216)))


class GameOfLife15(GameOfLife):
    def __init__(self):
        super().__init__(
            57,
            'GameOfLife15',
            ((120, 216), (128, 224)))


class GameOfLife16(GameOfLife):
    def __init__(self):
        super().__init__(
            58,
            'GameOfLife16',
            ((120, 192), (128, 200)))


class GameOfLife17(GameOfLife):
    def __init__(self):
        super().__init__(
            59,
            'GameOfLife17',
            ((120, 200), (128, 208)))


class GameOfLife18(GameOfLife):
    def __init__(self):
        super().__init__(
            60,
            'GameOfLife18',
            ((96, 128), (112, 160)))


class GameOfLife19(GameOfLife):
    def __init__(self):
        super().__init__(
            61,
            'GameOfLife19',
            ((96, 160), (112, 192)))


class GameOfLife20(GameOfLife):
    def __init__(self):
        super().__init__(
            62,
            'GameOfLife20',
            ((112, 160), (120, 176)))


class GameOfLife21(GameOfLife):
    def __init__(self):
        super().__init__(
            63,
            'GameOfLife21',
            ((112, 176), (120, 192)))


class GameOfLife22(GameOfLife):
    def __init__(self):
        super().__init__(
            64,
            'GameOfLife22',
            ((120, 176), (128, 184)))


class GameOfLife23(GameOfLife):
    def __init__(self):
        super().__init__(
            65,
            'GameOfLife23',
            ((120, 184), (128, 192)))


class GameOfLife24(GameOfLife):
    def __init__(self):
        super().__init__(
            66,
            'GameOfLife24',
            ((120, 160), (128, 168)))


class GameOfLife25(GameOfLife):
    def __init__(self):
        super().__init__(
            67,
            'GameOfLife25',
            ((120, 168), (128, 176)))


class GameOfLife26(GameOfLife):
    def __init__(self):
        super().__init__(
            68,
            'GameOfLife26',
            ((112, 128), (120, 144)))


class GameOfLife27(GameOfLife):
    def __init__(self):
        super().__init__(
            69,
            'GameOfLife27',
            ((112, 144), (120, 160)))


class GameOfLife28(GameOfLife):
    def __init__(self):
        super().__init__(
            70,
            'GameOfLife28',
            ((120, 144), (128, 152)))


class GameOfLife29(GameOfLife):
    def __init__(self):
        super().__init__(
            71,
            'GameOfLife29',
            ((120, 152), (128, 160)))


class GameOfLife30(GameOfLife):
    def __init__(self):
        super().__init__(
            72,
            'GameOfLife30',
            ((120, 128), (128, 136)))


class GameOfLife31(GameOfLife):
    def __init__(self):
        super().__init__(
            73,
            'GameOfLife31',
            ((120, 136), (128, 144)))


class GameOfLife32(GameOfLife):
    def __init__(self):
        super().__init__(
            74,
            'GameOfLife32',
            ((64, 0), (96, 64)))


class GameOfLife33(GameOfLife):
    def __init__(self):
        super().__init__(
            75,
            'GameOfLife33',
            ((64, 64), (96, 128)))


class GameOfLife34(GameOfLife):
    def __init__(self):
        super().__init__(
            76,
            'GameOfLife34',
            ((96, 64), (112, 96)))


class GameOfLife35(GameOfLife):
    def __init__(self):
        super().__init__(
            77,
            'GameOfLife35',
            ((96, 96), (112, 128)))


class GameOfLife36(GameOfLife):
    def __init__(self):
        super().__init__(
            78,
            'GameOfLife36',
            ((112, 96), (120, 112)))


class GameOfLife37(GameOfLife):
    def __init__(self):
        super().__init__(
            79,
            'GameOfLife37',
            ((112, 112), (120, 128)))


class GameOfLife38(GameOfLife):
    def __init__(self):
        super().__init__(
            80,
            'GameOfLife38',
            ((120, 112), (128, 120)))


class GameOfLife39(GameOfLife):
    def __init__(self):
        super().__init__(
            81,
            'GameOfLife39',
            ((120, 120), (128, 128)))


class GameOfLife40(GameOfLife):
    def __init__(self):
        super().__init__(
            82,
            'GameOfLife40',
            ((120, 96), (128, 104)))


class GameOfLife41(GameOfLife):
    def __init__(self):
        super().__init__(
            83,
            'GameOfLife41',
            ((120, 104), (128, 112)))


class GameOfLife42(GameOfLife):
    def __init__(self):
        super().__init__(
            84,
            'GameOfLife42',
            ((112, 64), (120, 80)))


class GameOfLife43(GameOfLife):
    def __init__(self):
        super().__init__(
            85,
            'GameOfLife43',
            ((112, 80), (120, 96)))


class GameOfLife44(GameOfLife):
    def __init__(self):
        super().__init__(
            86,
            'GameOfLife44',
            ((120, 80), (128, 88)))


class GameOfLife45(GameOfLife):
    def __init__(self):
        super().__init__(
            87,
            'GameOfLife45',
            ((120, 88), (128, 96)))


class GameOfLife46(GameOfLife):
    def __init__(self):
        super().__init__(
            88,
            'GameOfLife46',
            ((120, 64), (128, 72)))


class GameOfLife47(GameOfLife):
    def __init__(self):
        super().__init__(
            89,
            'GameOfLife47',
            ((120, 72), (128, 80)))


class GameOfLife48(GameOfLife):
    def __init__(self):
        super().__init__(
            90,
            'GameOfLife48',
            ((96, 0), (112, 32)))


class GameOfLife49(GameOfLife):
    def __init__(self):
        super().__init__(
            91,
            'GameOfLife49',
            ((96, 32), (112, 64)))


class GameOfLife50(GameOfLife):
    def __init__(self):
        super().__init__(
            92,
            'GameOfLife50',
            ((112, 32), (120, 48)))


class GameOfLife51(GameOfLife):
    def __init__(self):
        super().__init__(
            93,
            'GameOfLife51',
            ((112, 48), (120, 64)))


class GameOfLife52(GameOfLife):
    def __init__(self):
        super().__init__(
            94,
            'GameOfLife52',
            ((120, 48), (128, 56)))


class GameOfLife53(GameOfLife):
    def __init__(self):
        super().__init__(
            95,
            'GameOfLife53',
            ((120, 56), (128, 64)))


class GameOfLife54(GameOfLife):
    def __init__(self):
        super().__init__(
            96,
            'GameOfLife54',
            ((120, 32), (128, 40)))


class GameOfLife55(GameOfLife):
    def __init__(self):
        super().__init__(
            97,
            'GameOfLife55',
            ((120, 40), (128, 48)))


class GameOfLife56(GameOfLife):
    def __init__(self):
        super().__init__(
            98,
            'GameOfLife56',
            ((112, 0), (120, 16)))


class GameOfLife57(GameOfLife):
    def __init__(self):
        super().__init__(
            99,
            'GameOfLife57',
            ((112, 16), (120, 32)))


class GameOfLife58(GameOfLife):
    def __init__(self):
        super().__init__(
            100,
            'GameOfLife58',
            ((120, 16), (128, 24)))


class GameOfLife59(GameOfLife):
    def __init__(self):
        super().__init__(
            101,
            'GameOfLife59',
            ((120, 24), (128, 32)))


class GameOfLife60(GameOfLife):
    def __init__(self):
        super().__init__(
            102,
            'GameOfLife60',
            ((120, 0), (128, 8)))


class GameOfLife61(GameOfLife):
    def __init__(self):
        super().__init__(
            103,
            'GameOfLife61',
            ((120, 8), (128, 16)))
