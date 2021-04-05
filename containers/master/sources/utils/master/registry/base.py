from abc import ABC
from collections import defaultdict
from pprint import pformat
from queue import Queue
from threading import Lock
from threading import Thread
from time import sleep
from traceback import print_exc
from typing import DefaultDict
from typing import Dict
from typing import List

from .idManager import IDManager
from .registered import RegisteredManager
from .roles import Actor
from .roles import TaskExecutor
from .roles import User
from .roles.nameFactory import NameFactory
from .tools.prettyDecision import prettyDecision
from .types import TaskLabeled
from ..application.base import Application
from ..application.manager import ApplicationManager
from ..logger.allSystemPerformance import AllSystemPerformance
from ..messageHandler.tools.terminateMessage import terminateMessage
from ..messageHandler.tools.waitMessage import waitMessage
from ..profiler.base import MasterProfiler
from ..profiler.decisions import Decisions
from ..scheduler.base import BaseScheduler
from ..scheduler.policies.nsga.base import BaseNSGA
from ..scheduler.types import Decision
from ...component import BasicComponent
from ...connection.message.received import MessageReceived
from ...connection.message.toSend import MessageToSend
from ...types import Component
from ...types import ComponentRole
from ...types import SynchronizedAttribute
from ...types.hostProfiles import ActorResources
from ...types.message.subType import MessageSubType
from ...types.message.type import MessageType


class Registry(ABC):
    def __init__(
            self,
            basicComponent: BasicComponent,
            applicationManager: ApplicationManager,
            scheduler: BaseScheduler,
            systemPerformance: AllSystemPerformance,
            profiler: MasterProfiler,
            waitTimeout: int = 0):
        self.profiler = profiler
        self.systemPerformance = systemPerformance
        self.applicationManager = applicationManager
        self.basicComponent = basicComponent
        self.debugLogger = self.basicComponent.debugLogger
        self.idManager = IDManager()
        self.nameFactory = NameFactory(
            nameLogPrinting=self.basicComponent.nameLogPrinting)
        self.registeredManager = RegisteredManager()

        self.scheduler = scheduler
        self.decisionsQueue: Queue[Decision] = Queue()
        self.decisionHandlerThreadPool()

        self.decisions = Decisions()
        self.__schedulingNum = 0
        self.locks: DefaultDict[str, Lock] = defaultdict(lambda: Lock())
        self.decisionResultFromActor: Dict[Decision] = {}
        self.knowMasters = []
        self.requestQueue = Queue()
        self.scheduleLock = Lock()
        self.waitTimeout = waitTimeout

    def registerClient(self, message: MessageReceived):
        source = message.source
        if source.role is ComponentRole.USER:
            return self.registerUser(message)
        if source.role is ComponentRole.ACTOR:
            return self.registerActor(message)
        if source.role is ComponentRole.TASK_EXECUTOR:
            return self.registerTaskExecutor(message)
        return None

    def registerActor(self, message: MessageReceived):
        return self._registerActor(
            self, message, attributeName='registeredActor')

    def registerUser(self, message: MessageReceived):
        return self._registerUser(self, message, attributeName='registeredUser')

    def registerTaskExecutor(self, message: MessageReceived):
        return self._registerTaskExecutor(
            self, message, attributeName='registeredTaskExecutor')

    def deregisterActor(self, actor: Actor):
        return self._deregisterActor(
            self, actor, attributeName='registeredActor')

    def deregisterUser(self, user: User):
        return self._deregisterUser(
            self, user, attributeName='registeredUser')

    def deregisterTaskExecutor(self, taskExecutor: TaskExecutor):
        return self._deregisterTaskExecutor(
            self, taskExecutor, attributeName='registeredTaskExecutor')

    @SynchronizedAttribute
    def _registerActor(
            self, message: MessageReceived, attributeName='registeredActor'):
        source = message.source
        if source.hostID in self.registeredManager.actors:
            self.basicComponent.debugLogger.debug(
                'Duplicated Actor Registration Request: %s', str(source.addr))
            return terminateMessage(
                source,
                'Your host has another %s registered'
                ' at %s' % (
                    source.role.value,
                    str(self.basicComponent.me.addr)))
        data = message.data
        actorID = self.idManager.actor.next()
        actorResources = ActorResources.fromDict(data['actorResources'])

        name, nameLogPrinting, nameConsistent = self.nameFactory.nameActor(
            source, actorID)

        actor = Actor(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=source.addr,
            componentID=actorID,
            hostID=source.hostID,
            actorResources=actorResources)
        self.registeredManager.actors[actor] = actor
        self.profiler.updateActorResources(actor)
        data = {
            'actorID': actorID,
            'name': name,
            'nameLogPrinting': nameLogPrinting,
            'nameConsistent': nameConsistent}
        messageToRespond = MessageToSend(
            messageType=MessageType.REGISTRATION,
            messageSubType=MessageSubType.REGISTERED,
            data=data,
            destination=source)
        self.basicComponent.debugLogger.debug(
            'Registered: %s', nameLogPrinting)
        return messageToRespond

    @SynchronizedAttribute
    def _registerUser(
            self, message: MessageReceived, attributeName='registeredUser'):
        source = message.source
        data = message.data
        userID = self.idManager.user.next()
        applicationName = data['applicationName']
        label = data['label']
        if applicationName not in self.applicationManager.applications:
            return None
        application = self.applicationManager.applications[applicationName]
        applicationCopy: Application = application.copy(withLabel=label)
        name, nameLogPrinting, nameConsistent = self.nameFactory.nameUser(
            source, userID, applicationCopy)
        user = User(
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            addr=source.addr,
            componentID=userID,
            hostID=source.hostID,
            application=applicationCopy)
        self.registeredManager.users[user] = user
        try:
            schedulingSuccess = self.scheduler.schedule(
                user=user,
                registeredManager=self.registeredManager,
                resources=self.profiler.me.resources,
                systemPerformance=self.systemPerformance,
                basicComponent=self.basicComponent,
                decisionsQueue=self.decisionsQueue)
            if not schedulingSuccess:
                return
            self.checkTaskExecutorForUser(user=user)
        except Exception as e:
            print_exc()
            if isinstance(self.scheduler, BaseNSGA):
                self.scheduler.lock.release()
                self.scheduler.leaveWaiting()
            return terminateMessage(component=user, reason=str(e))

    @SynchronizedAttribute
    def _registerTaskExecutor(self, message: MessageReceived,
                              attributeName='registeredTaskExecutor'):
        data = message.data
        source = message.source
        taskExecutorID = self.idManager.taskExecutor.next()

        userID = data['userID']
        actorID = data['actorID']

        if userID not in self.registeredManager.users:
            return terminateMessage(source, 'Invalid userID')
        user: User = self.registeredManager.users[userID]

        if actorID not in self.registeredManager.actors:
            return terminateMessage(source, 'Invalid actorID')
        actor = self.registeredManager.actors[actorID]
        taskName = data['taskName']
        taskToken = data['taskToken']
        taskLabeled = TaskLabeled.fromDict(
            {
                'name': taskName,
                'token': taskToken,
                'label': user.application.label})
        claimSuccess = user.claimTask(
            hostID=actor.hostID,
            taskNameLabeled=taskLabeled.nameLabeled,
            taskToken=taskToken)
        if not claimSuccess:
            return terminateMessage(source, 'This Task does not belong to you')

        name, nameLogPrinting, nameConsistent = \
            self.nameFactory.nameTaskExecutor(
                source, taskExecutorID, taskLabeled, user, actor)

        taskExecutor = TaskExecutor(
            actorID=actorID,
            userID=userID,
            task=taskLabeled,
            addr=source.addr,
            componentID=taskExecutorID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            hostID=actor.hostID,
            waitTimeout=self.waitTimeout)
        self.registeredManager.taskExecutors[taskExecutor] = taskExecutor
        data = {
            'taskExecutorID': taskExecutorID,
            'name': taskExecutor.name,
            'nameLogPrinting': taskExecutor.nameLogPrinting,
            'nameConsistent': taskExecutor.nameConsistent,
            'actorHostID': actor.hostID}
        self.basicComponent.sendMessage(
            messageType=MessageType.REGISTRATION,
            messageSubType=MessageSubType.REGISTERED,
            data=data,
            destination=source)
        self.basicComponent.debugLogger.debug(
            'Registered: %s ', nameLogPrinting)

    @SynchronizedAttribute
    def _deregisterActor(
            self, source: Component,
            attributeName='registeredActor'):
        if source.componentID not in self.registeredManager.actors:
            return terminateMessage(source, reason='Not registered')
        del self.registeredManager.actors[source.componentID]
        del self.registeredManager.actors[source.hostID]
        del self.registeredManager.actors[source.addr[0]]

    @SynchronizedAttribute
    def _deregisterUser(
            self, source: Component,
            attributeName='registeredUser'):
        if source.componentID not in self.registeredManager.users:
            return terminateMessage(source, reason='Not registered')
        user = self.registeredManager.users[source.componentID]
        for taskExecutor in user.taskNameToExecutor.values():
            if taskExecutor.waitTimeout <= 0:
                continue
            message = waitMessage(taskExecutor=taskExecutor)
            self.registeredManager.taskExecutors.coolOff(taskExecutor)
            self.basicComponent.sendMessage(messageToSend=message)
        del self.registeredManager.users[source.componentID]

    @SynchronizedAttribute
    def _deregisterTaskExecutor(
            self, source: Component,
            attributeName='registeredTaskExecutor'):
        if source.componentID not in self.registeredManager.taskExecutors:
            return terminateMessage(source, reason='Not registered')
        taskExecutor = self.registeredManager.taskExecutors[source.componentID]
        if taskExecutor.userID not in self.registeredManager.users:
            del self.registeredManager.taskExecutors[source.componentID]
            return terminateMessage(source, reason='Deregister')
        user = self.registeredManager.users[taskExecutor.userID]
        self._deregisterUser(self, source=user, attributeName='registeredUser')
        return terminateMessage(source, reason='Deregister')

    def checkTaskExecutorForUser(self, user: User):
        Thread(
            target=self._checkTaskExecutorForUser,
            args=(user,),
            name='ResourcesPlacement-%s' % user.nameLogPrinting).start()

    def _checkTaskExecutorForUser(self, user: User):
        totalTaskCount = len(user.taskNameList)
        while True:
            sleep(15)
            if user.componentID not in self.registeredManager.users:
                break
            unclaimedTaskCount = user.countUnclaimedTask()
            if unclaimedTaskCount == 0:
                break

            self.debugLogger.debug(
                '%s resources: %d/%d -> %s',
                user.nameLogPrinting,
                unclaimedTaskCount - unclaimedTaskCount,
                totalTaskCount,
                pformat(user.unclaimedTasks))

            self.resourcePlace(user=user)

    def decisionHandlerThreadPool(self):
        Thread(target=self.handleDecision, name='DecisionHandler').start()

    def handleDecision(self):
        while True:
            decision = self.decisionsQueue.get()
            self.printDecision(decision)
            hostIDSequence = decision.hostIDSequence()
            user = decision.user
            for i, hostID in enumerate(hostIDSequence):
                actor = self.registeredManager.actors[hostID]
                taskNameLabeled = user.application.taskNameList[i]
                taskToken = user.taskNameToToken[taskNameLabeled]
                childrenTaskTokens = self.findChildrenTaskTokens(
                    taskNameLabeled=taskNameLabeled, user=user)
                user.assignTask(
                    actor=actor,
                    taskNameLabeled=taskNameLabeled,
                    taskToken=taskToken,
                    childrenTaskTokens=childrenTaskTokens)
            self.resourcePlace(user=user)

    def printDecision(self, decision: Decision):
        evaluationRecord = decision.evaluationRecord
        evaluationRecord = [round(record, 2) for record in evaluationRecord]
        logLevel = self.basicComponent.debugLogger.level
        if logLevel != 20:
            records = '\n    EvaluationRecords:\n' \
                      '        %s' % str(evaluationRecord)
        else:
            records = ''
        self.basicComponent.debugLogger.info(
            '\n========== Scheduling Summary ==========\n'
            '    %s Scheduling used time: %f ms\n'
            '    %s Estimated:\n'
            '         ResponseTime for %s: %f ms\n'
            '    Details:\n'
            '%s%s'
            '\n========================================',
            self.scheduler.name,
            decision.schedulingTime,
            self.scheduler.name,
            decision.user.application.nameWithLabel,
            decision.cost,
            prettyDecision(decision, self.registeredManager.actors),
            records)

    @staticmethod
    def findChildrenTaskTokens(taskNameLabeled: str, user: User) \
            -> List[str]:
        application = user.application
        taskName = taskNameLabeled[:taskNameLabeled.find('-')]
        taskWithDependency = application.tasksWithDependency[taskName]
        childrenTaskTokens = []
        for childTask in taskWithDependency.children:
            if childTask.name == 'Actuator':
                continue
            if user.application.label == '':
                childTaskName = childTask.name
            else:
                childTaskName = '%s-%s' % (childTask.name, application.label)
            childTaskToken = user.taskNameToToken[childTaskName]
            childrenTaskTokens.append(childTaskToken)
        return childrenTaskTokens

    def resourcePlace(self, user: User):
        user.lock.acquire()
        for compactedKey in user.unclaimedTasks:
            hostID, taskNameLabeled, taskToken = compactedKey
            coolTaskExecutors = self.registeredManager.coolTaskExecutors
            childrenTaskTokens = user.unclaimedTasks[compactedKey]

            if hostID in coolTaskExecutors:
                if taskNameLabeled in coolTaskExecutors[hostID]:
                    if len(coolTaskExecutors[hostID][taskNameLabeled]):
                        self.sendReuseTaskExecutorMsg(
                            hostID=hostID,
                            user=user,
                            taskNameLabeled=taskNameLabeled,
                            taskToken=taskToken,
                            childrenTaskTokens=childrenTaskTokens)
                        continue
            self.sendInitTaskExecutorMsg(
                hostID=hostID,
                user=user,
                taskNameLabeled=taskNameLabeled,
                taskToken=taskToken,
                childrenTaskTokens=childrenTaskTokens)
        user.lock.release()

    def sendReuseTaskExecutorMsg(
            self,
            hostID: str,
            user: User,
            taskNameLabeled: str,
            taskToken: str,
            childrenTaskTokens: List[str]):
        taskName = taskNameLabeled[:taskNameLabeled.find('-')]
        coolTaskExecutors = self.registeredManager.coolTaskExecutors
        coolingSet = coolTaskExecutors[hostID][taskNameLabeled]
        taskExecutor = coolingSet.pop()
        data = {
            'taskName': taskName,
            'taskToken': taskToken,
            'userID': user.componentID,
            'childrenTaskTokens': childrenTaskTokens}
        self.basicComponent.sendMessage(
            messageType=MessageType.PLACEMENT,
            messageSubType=MessageSubType.REUSE,
            data=data,
            destination=taskExecutor)
        self.basicComponent.debugLogger.debug(
            'Reuse %s', taskExecutor.nameLogPrinting)

    def sendInitTaskExecutorMsg(
            self,
            hostID: str,
            user: User,
            taskNameLabeled: str,
            taskToken: str,
            childrenTaskTokens: List[str]):
        actor = self.registeredManager.actors[hostID]
        data = {
            'userName': user.name,
            'taskName': taskNameLabeled,
            'taskToken': taskToken,
            'label': user.application.label,
            'userID': user.componentID,
            'childrenTaskTokens': childrenTaskTokens}
        self.basicComponent.sendMessage(
            messageType=MessageType.PLACEMENT,
            messageSubType=MessageSubType.RUN_TASK_EXECUTOR,
            data=data,
            destination=actor)
