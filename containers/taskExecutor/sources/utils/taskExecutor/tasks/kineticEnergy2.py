from .base import BaseTask


class KineticEnergy2(BaseTask):
    def __init__(self):
        super().__init__(taskID=106, taskName='KineticEnergy2')
        self.m = None
        self.v0square = None
        self.v1square = None

    def exec(self, inputData):
        if 'v0square' in inputData:
            self.m = inputData['m']
            self.v0square = inputData['v0square']
            if self.v1square is None:
                return None

        if 'v1square' in inputData:
            self.v1square = inputData['v1square']
            if self.v0square is None:
                return None

        return self.m * (self.v1square - self.v0square)
