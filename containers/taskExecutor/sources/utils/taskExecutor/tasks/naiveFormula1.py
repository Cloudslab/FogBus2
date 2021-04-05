from .base import BaseTask


class NaiveFormula1(BaseTask):
    def __init__(self):
        super().__init__(taskID=109, taskName='NaiveFormula1')

    def exec(self, inputData):
        a = inputData['a']
        b = inputData['b']
        c = inputData['c']

        result = a * a / (b * b + c * c)
        inputData['resultPart1'] = result

        inputData['a'] += 1
        inputData['b'] += 1
        inputData['c'] += 1

        return inputData
