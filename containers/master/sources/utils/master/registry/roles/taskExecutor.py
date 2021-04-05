from threading import Event
from threading import Lock
from typing import Dict

from ..types import TaskLabeled
from ....types.basic.address import Address
from ....types.component import Component
from ....types.component.role import ComponentRole


class TaskExecutor(Component):
    def __init__(
            self,
            actorID: str,
            userID: str,
            task: TaskLabeled,
            addr: Address = ('0.0.0.0', 0),
            hostID: str = None,
            componentID: str = None,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            waitTimeout: int = 0):
        Component.__init__(
            self,
            role=ComponentRole.TASK_EXECUTOR,
            addr=addr,
            hostID=hostID,
            componentID=componentID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent)
        self.lock = Lock()
        self.actorID = actorID
        self.userID = userID
        self.task = task
        self.ready: Event = Event()
        self.waiting = False
        self.waitTimeout = waitTimeout

    @staticmethod
    def fromDict(inDict: Dict):
        taskExecutor = TaskExecutor(
            componentID=inDict['componentID'],
            addr=inDict['addr'],
            name=inDict['name'],
            nameLogPrinting=inDict['nameLogPrinting'],
            nameConsistent=inDict['nameConsistent'],
            hostID=inDict['hostID'],
            actorID=inDict['actorID'],
            userID=inDict['userID'],
            task=TaskLabeled.fromDict(inDict['task']),
            waitTimeout=inDict['waitTimeout'])
        return taskExecutor

    def toDict(self) -> Dict:
        inDict = {
            'role': self.role,
            'componentID': self.componentID,
            'addr': self.addr,
            'name': self.name,
            'nameLogPrinting': self.nameLogPrinting,
            'nameConsistent': self.nameConsistent,
            'hostID': self.hostID,
            'actorID': self.actorID,
            'userID': self.userID,
            'waitTimeout': self.waitTimeout,
            'task': self.task.toDict()}
        return inDict
