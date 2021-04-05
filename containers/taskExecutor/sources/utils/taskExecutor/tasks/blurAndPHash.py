import cv2
import numpy as np

from .base import BaseTask


class BlurAndPHash(BaseTask):
    def __init__(self):
        super().__init__(taskID=4, taskName='BlurAndPHash')
        self.thresholdLaplacian = 120
        self.thresholdDiffStop = 120
        self.thresholdDiffPre = 25
        self.hashLen = 32
        self.preStopPHash = None
        self.prePHash = None
        self.n = 0

    def exec(self, inputData):
        frame, isLastFrame = inputData
        if isLastFrame:
            return None, isLastFrame

        currPHash = self.getPHash(frame)
        if currPHash is None:
            return None

        if self.preStopPHash is None:
            self.preStopPHash = currPHash
            self.prePHash = currPHash
            return frame, isLastFrame

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

        medianValue = sum(matrixFlatten) * 1. / len(matrixFlatten)
        pHash = 0
        for i in matrixFlatten:
            pHash <<= 1
            if i >= medianValue:
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
