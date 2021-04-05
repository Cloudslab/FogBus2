from .base import BaseTask


class TestTask(BaseTask):
    def __init__(self, appID: int):
        super().__init__(appID, 'TestApp')

    def exec(self, inputData):
        return inputData * 2
