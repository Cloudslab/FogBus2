from .tools import terminateMessage
from .tools.waitMessage import waitMessage
from ..registry.base import Registry
from ..registry.roles.taskExecutor import TaskExecutor
from ..registry.roles.user import User
from ...component import BasicComponent
from ...connection import HandlerReturn
from ...connection import MessageReceived
from ...types import ComponentRole
from ...types import MessageSubType
from ...types import MessageType


class AcknowledgementHandler:

    def __init__(
            self,
            registry: Registry,
            basicComponent: BasicComponent, ):

        self.registry = registry
        self.basicComponent = basicComponent

    def handleReady(self, message: MessageReceived) -> HandlerReturn:
        source = message.source
        if source.role is not ComponentRole.TASK_EXECUTOR:
            return terminateMessage(source)

        nameConsistent = source.nameConsistent
        if nameConsistent not in self.registry.registeredManager.taskExecutors:
            return
        taskExecutor: TaskExecutor = \
            self.registry.registeredManager.taskExecutors[nameConsistent]
        taskExecutor.ready.set()

        userID = taskExecutor.userID
        if userID not in self.registry.registeredManager.users:
            self.registry.registeredManager.taskExecutors.coolOff(taskExecutor)
            responseMessage = waitMessage(taskExecutor=taskExecutor)
            self.basicComponent.sendMessage(messageToSend=responseMessage)
            return
        user: User = self.registry.registeredManager.users[userID]

        user.lock.acquire()
        user.taskNameToExecutor[taskExecutor.task.nameLabeled] = taskExecutor
        if not len(user.taskNameToExecutor) == len(user.taskNameList):
            user.lock.release()
            return
        for otherExecutor in user.taskNameToExecutor.values():
            # TODO: Not efficient
            if not otherExecutor.ready.isSet():
                user.lock.release()
                return
        if user.isReady:
            user.lock.release()
            return
        user.isReady = True
        self.basicComponent.sendMessage(
            messageType=MessageType.ACKNOWLEDGEMENT,
            messageSubType=MessageSubType.SERVICE_READY,
            data={},
            destination=user)
        self.basicComponent.debugLogger.debug(
            '%s is ready to run. ' % user.nameLogPrinting)
        user.lock.release()
        return

    def handleTaskExecutorWaiting(
            self, message: MessageReceived) -> HandlerReturn:
        source = message.source
        registeredManager = self.registry.registeredManager
        if source.componentID not in registeredManager.taskExecutors:
            return None
        taskExecutor = registeredManager.taskExecutors[source.componentID]
        actorID = taskExecutor.actorID
        if actorID not in registeredManager.actors:
            return
        actor = registeredManager.actors[actorID]
        actorHostId = actor.hostID
        coolTaskExecutors = registeredManager.coolTaskExecutors

        if actorHostId not in coolTaskExecutors:
            coolTaskExecutors[actorHostId] = {}

        taskNameLabeled = taskExecutor.task.nameLabeled

        if taskNameLabeled not in coolTaskExecutors[actorHostId]:
            coolTaskExecutors[actorHostId][taskNameLabeled] = set([])

        coolTaskExecutors[actorHostId][taskNameLabeled].add(taskExecutor)
        self.basicComponent.debugLogger.debug(
            'Cool off %s', taskExecutor.nameLogPrinting)
