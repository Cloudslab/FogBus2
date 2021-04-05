import os

import cv2

from .base import BaseTask


class FaceDetection(BaseTask):

    def __init__(self):
        super().__init__(taskID=1, taskName='FaceDetection')
        absDir = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        classifierPath = os.path.join(absDir, '../cascade/haar-face.xml')
        classifierPath = os.path.abspath(classifierPath)
        self.face_cascade = cv2.CascadeClassifier(classifierPath)

    def exec(self, inputData):
        # print('FaceDetection',str(inputData)[:15])
        frame = inputData
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        result = []
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            result.append((x, y, w, h, roi_gray))
        # print('FaceDetection',str(result)[:15], ' <-')
        return result
