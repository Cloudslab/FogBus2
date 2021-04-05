from .base import BaseTask


class KineticEnergy0(BaseTask):
    def __init__(self):
        super().__init__(taskID=104, taskName='KineticEnergy0')

    def exec(self, inputData):
        m, v0 = inputData['m'], inputData['v0']
        v0Square = v0 * v0
        inputData['v0Square'] = v0Square
        return inputData
