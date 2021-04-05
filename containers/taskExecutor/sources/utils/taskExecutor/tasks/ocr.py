import editdistance
import pytesseract

from .base import BaseTask


class OCR(BaseTask):
    def __init__(self):
        super().__init__(taskID=5, taskName='OCR')
        self.text = ''
        self.preText = None
        self.thresholdEditDistance = 800

    def exec(self, inputData):
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
