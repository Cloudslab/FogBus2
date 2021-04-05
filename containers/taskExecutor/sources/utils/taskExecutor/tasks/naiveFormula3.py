from .base import BaseTask


class NaiveFormula3(BaseTask):
    def __init__(self):
        super().__init__(taskID=111, taskName='NaiveFormula3')
        self.resultPart0 = None
        self.resultPart1 = None
        self.resultPart2 = None

    def exec(self, inputData):
        if 'resultPart0' in inputData:
            self.resultPart0 = inputData['resultPart0']
        if 'resultPart1' in inputData:
            self.resultPart1 = inputData['resultPart1']
        if 'resultPart2' in inputData:
            self.resultPart2 = inputData['resultPart2']
        if self.resultPart0 is None:
            return
        if self.resultPart1 is None:
            return
        if self.resultPart2 is None:
            return
        finalResult = self.resultPart0 + self.resultPart1 + self.resultPart2
        inputData['resultPart0'] = self.resultPart0
        inputData['resultPart1'] = self.resultPart1
        inputData['resultPart2'] = self.resultPart2
        inputData['finalResult'] = finalResult
        return inputData
