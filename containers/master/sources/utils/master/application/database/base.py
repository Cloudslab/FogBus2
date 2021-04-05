from abc import abstractmethod
from typing import List

from ..base import Application
from ..task.base import Task


class BaseDatabase:
    @abstractmethod
    def readTasks(self) -> List[Task]:
        pass

    @abstractmethod
    def writeTask(self, task: Task):
        pass

    @abstractmethod
    def readApplications(self) -> List[Application]:
        pass

    @abstractmethod
    def writeApplication(self, application: Application):
        pass
