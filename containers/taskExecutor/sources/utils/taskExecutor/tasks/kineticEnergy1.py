from .base import BaseTask


class KineticEnergy1(BaseTask):
    def __init__(self):
        super().__init__(taskID=105, taskName='KineticEnergy1')

    def exec(self, inputData):
        m, v1 = inputData['m'], inputData['v1']
        v1Square = v1 * v1
        inputData['v1Square'] = v1Square
        return inputData
