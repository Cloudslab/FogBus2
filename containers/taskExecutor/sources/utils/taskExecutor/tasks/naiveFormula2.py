from .base import BaseTask


class NaiveFormula2(BaseTask):
    def __init__(self):
        super().__init__(taskID=110, taskName='NaiveFormula2')

    def exec(self, inputData):
        a = inputData['a']
        b = inputData['b']
        c = inputData['c']

        result = 1 / a + 2 / b + 3 / c
        inputData['resultPart2'] = result
        return inputData
