import os

import cv2

from .base import BaseTask


class EyeDetection(BaseTask):

    def __init__(self):
        super().__init__(taskID=2, taskName='EyeDetection')
        absDir = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        classifierPath = os.path.join(absDir, '../cascade/haar-eye.xml')
        classifierPath = os.path.abspath(classifierPath)
        self.eye_cascade = cv2.CascadeClassifier(classifierPath)

    def exec(self, inputData):
        # print('EyeDetection', str(inputData)[:15])
        faces = inputData
        for i, (x, y, w, h, roi_gray) in enumerate(faces):
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            faces[i] = (x, y, w, h, eyes)
        # print('EyeDetection', str(faces)[:15], ' <-')
        return faces
