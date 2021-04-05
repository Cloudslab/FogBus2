from .base import BaseTask


class NaiveFormula0(BaseTask):
    def __init__(self):
        super().__init__(taskID=108, taskName='NaiveFormula0')

    def exec(self, inputData):
        a = inputData['a']
        b = inputData['b']
        c = inputData['c']

        result = a + b + c
        inputData['resultPart0'] = result

        inputData['a'] += 1
        inputData['b'] += 1
        inputData['c'] += 1

        return inputData
