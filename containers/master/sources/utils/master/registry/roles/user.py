from threading import Lock
from typing import Dict
from typing import List
from typing import Tuple

from .actor import Actor
from .taskExecutor import TaskExecutor
from .tools import generateTokenList
from ...application.base import Application
from ....types.basic.address import Address
from ....types.component import Component
from ....types.component import ComponentRole


class User(Component):
    def __init__(
            self,
            application: Application,
            taskNameToExecutor: Dict[str, TaskExecutor] = None,
            addr: Address = ('0.0.0.0', 0),
            hostID: str = None,
            componentID: str = None,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            tokenList: List[str] = None):
        Component.__init__(
            self,
            role=ComponentRole.USER,
            addr=addr,
            hostID=hostID,
            componentID=componentID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent)
        self.application = application
        self.taskNameList = application.taskNameList
        self.entryTaskNameList = application.entryTaskNameList
        self.tokenList = tokenList
        if self.tokenList is None:
            self.tokenList = generateTokenList(len(self.taskNameList))
        self.taskNameToToken: Dict[str, str] = self.generateTaskNameToToken()
        self.taskNameToExecutor = taskNameToExecutor
        if self.taskNameToExecutor is None:
            self.taskNameToExecutor: Dict[str, TaskExecutor] = {}

        self.unclaimedTasks: Dict[Tuple[str, str, str], List[str]] = {}
        self.lock: Lock = Lock()
        self.isReady = False

    def generateTaskNameToToken(self) -> Dict[str, str]:
        inDict = {}
        for i, taskName in enumerate(self.taskNameList):
            inDict[taskName] = self.tokenList[i]
        return inDict

    def assignTask(
            self,
            actor: Actor,
            taskNameLabeled: str,
            taskToken: str,
            childrenTaskTokens: List[str]):
        compactedKey = (actor.hostID, taskNameLabeled, taskToken)
        self.lock.acquire()
        self.unclaimedTasks[compactedKey] = childrenTaskTokens
        self.lock.release()

    def claimTask(self, hostID: str, taskNameLabeled: str, taskToken: str) \
            -> bool:
        compactedKey = (hostID, taskNameLabeled, taskToken)
        self.lock.acquire()
        if compactedKey not in self.unclaimedTasks:
            self.lock.release()
            return False
        del self.unclaimedTasks[compactedKey]
        self.lock.release()
        return True

    def countUnclaimedTask(self) -> int:
        self.lock.acquire()
        count = len(self.unclaimedTasks)
        self.lock.release()
        return count

    @staticmethod
    def fromDict(inDict: Dict):
        user = User(
            componentID=inDict['componentID'],
            addr=inDict['addr'],
            name=inDict['name'],
            nameLogPrinting=inDict['nameLogPrinting'],
            nameConsistent=inDict['nameConsistent'],
            hostID=inDict['hostID'],
            application=Application.fromDict(inDict['application']),
            tokenList=inDict['tokenList'])
        return user

    def toDict(self) -> Dict:
        inDict = {
            'role': self.role,
            'componentID': self.componentID,
            'addr': self.addr,
            'name': self.name,
            'nameLogPrinting': self.nameLogPrinting,
            'nameConsistent': self.nameConsistent,
            'hostID': self.hostID,
            'application': self.application.toDict(),
            'tokenList': self.tokenList, }
        return inDict
