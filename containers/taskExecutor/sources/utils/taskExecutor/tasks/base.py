from abc import abstractmethod

from ...types import ProcessingTime
from ...types import SequenceMedian


class BaseTask:

    def __init__(self, taskID: int, taskName: str):
        self.taskID = taskID
        self.taskName = taskName
        self.taskCalls = 0
        self.processingTime = SequenceMedian()
        self.medianProcessingTime = ProcessingTime(
            taskExecutorName=taskName)
        self.processedCount = 0

    @abstractmethod
    def exec(self, inputData):
        pass

    def updateProcessingTime(self, processingTime: float):
        self.processingTime.update(processingTime)
        self.medianProcessingTime.processingTime = self.processingTime.median()
