from typing import Dict
from typing import Set
from typing import Tuple
from typing import Union

from .base import Registered
from ..roles import TaskExecutor
from ....types import Address

MapUnion = Union[str, str, str, Address]
MapTuple = Tuple[str, str, str, Address]


class RegisteredTaskExecutors(Registered):

    def __init__(self):
        Registered.__init__(self)
        self.keyMap: Dict[MapUnion, MapTuple] = {}
        self.inCoolOffPeriod: Dict[str, Set[TaskExecutor]] = {}

    def __setitem__(self, key, taskExecutor: TaskExecutor):
        self._setitem(key=key, taskExecutor=taskExecutor)

    def __delitem__(self, key):
        self._delitem(key)

    def __contains__(self, taskExecutor: TaskExecutor) -> bool:
        return self._contains(taskExecutor=taskExecutor)

    def __getitem__(self, key) -> TaskExecutor:
        return self._getitem(key)

    def _setitem(self, key, taskExecutor):
        self.lock.acquire()
        componentID = taskExecutor.componentID
        nameConsistent = taskExecutor.nameConsistent
        task = taskExecutor.task
        addr = taskExecutor.addr
        self.dict.__setitem__(componentID, taskExecutor)
        self.dict.__setitem__(nameConsistent, taskExecutor)
        self.dict.__setitem__(task.token, taskExecutor)
        self.dict.__setitem__(addr, taskExecutor)
        t = (componentID, nameConsistent, task.token, addr)
        self.keyMap[componentID] = t
        self.keyMap[nameConsistent] = t
        self.keyMap[task.token] = t
        self.keyMap[addr] = t
        self.lock.release()

    def _getitem(self, key) -> TaskExecutor:
        self.lock.acquire()
        taskExecutor = self.dict[key]
        self.lock.release()
        return taskExecutor

    def _delitem(self, key):
        self.lock.acquire()
        componentID, nameConsistent, taskToken, addr = self.keyMap[key]
        try:
            del self.dict[componentID]
            del self.dict[nameConsistent]
            del self.dict[taskToken]
            del self.dict[addr]
            del self.keyMap[componentID]
            del self.keyMap[nameConsistent]
            del self.keyMap[taskToken]
            del self.keyMap[addr]
        except KeyError:
            pass
        self.lock.release()

    def _contains(self, taskExecutor: TaskExecutor) -> bool:
        self.lock.acquire()
        ret = False
        if isinstance(taskExecutor, str):
            if taskExecutor in self.dict:
                ret = True
            self.lock.release()
            return ret
        if not isinstance(taskExecutor, TaskExecutor):
            self.lock.release()
            return False
        elif taskExecutor.componentID in self.dict:
            ret = True
        elif taskExecutor.nameConsistent in self.dict:
            ret = True
        elif taskExecutor.task.token in self.dict:
            ret = True
        elif taskExecutor.addr in self.dict:
            ret = True
        self.lock.release()
        return ret

    def coolOff(self, taskExecutor: TaskExecutor):
        if not self.__contains__(taskExecutor):
            return
        taskExecutor.lock.acquire()
        taskExecutor.task.token = ''
        taskExecutor.waiting = True
        nameConsistent = taskExecutor.nameConsistent
        if nameConsistent not in self.inCoolOffPeriod:
            self.inCoolOffPeriod[taskExecutor.nameConsistent] = set()
        self.inCoolOffPeriod[taskExecutor.nameConsistent].add(taskExecutor)
        taskExecutor.lock.release()

    def getFromCoolOff(self, nameConsistent: str):
        if nameConsistent not in self.inCoolOffPeriod:
            return
        taskExecutor = self.inCoolOffPeriod[nameConsistent].pop()
        return taskExecutor
