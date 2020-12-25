import logging
from queue import Queue
from logger import get_logger
from datatype import Task
from typing import NoReturn


class TaskManager:

    def __init__(self, logLevel=logging.DEBUG):
        self.currentTaskID = 0
        self.waitingTasks: Queue[Task] = Queue()
        self.finishedTasks: Queue[Task] = Queue()
        self.processingTasks: dict[int, Task] = {}
        self.logger = get_logger('TaskManager', logLevel)

    def submit(self, workerID: int, userID: int, appID: int, dataID: int) -> Task:
        # TODO: racing
        self.currentTaskID += 1
        taskID = self.currentTaskID
        task = Task(
            workerID=workerID,
            userID=userID,
            taskID=taskID,
            appID=appID,
            dataID=dataID)
        self.processingTasks[taskID] = task
        # self.waitingTasks.put(task)
        return task

    def getUnfinishedTask(self, workerID: int) -> Task:
        task = self.waitingTasks.get(block=False)
        task.workerID = workerID
        self.processingTasks[task.taskID] = task
        return task

    def getFinishedTask(self) -> Task:
        task = self.finishedTasks.get(block=False)
        return task

    def finish(self, taskID, resultID: int):
        if taskID in self.processingTasks:
            task = self.processingTasks[taskID]
            task.resultID = resultID
            task.hasDone = True
            self.finishedTasks.put(task)
            del self.processingTasks[taskID]
