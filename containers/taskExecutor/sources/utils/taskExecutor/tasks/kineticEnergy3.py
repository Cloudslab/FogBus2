from .base import BaseTask


class KineticEnergy3(BaseTask):
    def __init__(self):
        super().__init__(taskID=107, taskName='KineticEnergy3')
        self.constant = 1 / 2

    def exec(self, inputData):
        return self.constant * inputData
