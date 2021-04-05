from abc import abstractmethod
from queue import Queue
from threading import Lock
from typing import Union

from .baseScaler.base import Scaler
from .types import Decision
from ..logger.allSystemPerformance import AllSystemPerformance
from ..registry.registered.manager import RegisteredManager
from ..registry.roles import User
from ...component.basic import BasicComponent
from ...types import Component
from ...types import ComponentRole
from ...types.hostProfiles.resources import Resources
from ...types.message import MessageSubType
from ...types.message import MessageType


class BaseScheduler:

    def __init__(
            self, schedulerName: str, isContainerMode: bool, *args, **kwargs):
        self.isContainerMode = isContainerMode
        self.name = schedulerName
        self._waitingCountLock = Lock()
        self._waitingCount = 0
        self.scaler: Scaler = None

    def schedule(
            self,
            user: User,
            registeredManager: RegisteredManager,
            resources: Resources,
            systemPerformance: AllSystemPerformance,
            basicComponent: BasicComponent,
            decisionsQueue: Queue[Decision],
            *args,
            **kwargs) -> bool:
        allActors = registeredManager.actors.copyAll()

        if not len(allActors):
            basicComponent.debugLogger.warning(
                'No %s to schedule', ComponentRole.ACTOR.value)
            self.scaler.warnUser(user)
            return False

        if resources.cpu.utilization > .8:
            schedulingCount = self.readWaitingCount()
            if schedulingCount > 4:
                knownMasters = registeredManager.masters.copyAll()
                subMaster = self.getBestMaster(
                    user=user, knownMasters=knownMasters)
                if subMaster is None:
                    self.scaler = self.prepareScaler(
                        user=user,
                        master=basicComponent.me,
                        allActors=allActors,
                        systemPerformance=systemPerformance,
                        isContainerMode=self.isContainerMode)
                    subMaster = self.scaler.scale(user=user, actors=allActors)
                    if subMaster is None:
                        return False
                basicComponent.debugLogger.debug(
                    'Forward request to another ip %s', str(subMaster.addr[0]))
                self.scaler.notifyUser(user, subMaster)
                return False

        decision = self._schedule(
            user=user,
            master=basicComponent.me,
            allActors=allActors,
            systemPerformance=systemPerformance,
            isContainerMode=self.isContainerMode,
            *args,
            **kwargs)
        decisionsQueue.put(decision)
        data = {
            'userID': user.componentID,
            'name': user.name,
            'nameLogPrinting': user.nameLogPrinting,
            'nameConsistent': user.nameConsistent}

        basicComponent.sendMessage(
            messageType=MessageType.REGISTRATION,
            messageSubType=MessageSubType.REGISTERED,
            data=data,
            destination=user)
        basicComponent.debugLogger.debug('Registered: %s', user.nameLogPrinting)
        return True

    @abstractmethod
    def _schedule(self, *args, **kwargs) -> Decision:
        raise NotImplementedError

    def joinWaiting(self):
        self._waitingCountLock.acquire()
        self._waitingCount += 1
        self._waitingCountLock.release()

    def leaveWaiting(self):
        self._waitingCountLock.acquire()
        self._waitingCount -= 1
        self._waitingCountLock.release()

    def readWaitingCount(self):
        self._waitingCountLock.acquire()
        count = self._waitingCount
        self._waitingCountLock.release()
        return count

    @abstractmethod
    def getBestMaster(
            self, *args, **kwargs) -> Union[Component, None]:
        raise NotImplementedError

    @abstractmethod
    def prepareScaler(self, *args, **kwargs) -> Scaler:
        raise NotImplementedError

    def genUserTaskToken(self, user: User):
        pass
