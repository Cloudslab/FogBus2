import cv2
import pytesseract
import editdistance
import numpy as np
from datatype import TasksWorkerSide


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
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
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
