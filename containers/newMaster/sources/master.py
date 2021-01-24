import logging
import sys
import os
from logger import get_logger
from registry import Registry
from connection import Message
from node import Node
from profilerManage import Profiler
from scheduling import Scheduler, NSGA3
from typing import Tuple

Address = Tuple[str, int]


class Master(Node, Profiler):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            schedulerName: str = None,
            masterID: int = 0,
            logLevel=logging.DEBUG):

        Profiler.__init__(self)
        Node.__init__(
            self,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self._saveToPersistentStorage, 2),
                (self.__requestProfiler, 2)],
            logLevel=logLevel
        )

        self.id = masterID
        self.scheduler: Scheduler = self.__getScheduler(
            schedulerName=schedulerName)
        self.registry: Registry = Registry(
            scheduler=self.scheduler)

    def __getScheduler(self, schedulerName: str) -> Scheduler:
        if schedulerName in {None, 'NSGA3'}:
            return NSGA3(
                edges=self.edges,
                averageProcessTime=self.averageProcessTime,
                generationNum=10)
        self.logger.warning('Unknown scheduler: %s', schedulerName)
        os._exit(0)

    def run(self):
        self.role = 'Master'
        self.setName()
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.logger.info("Serving ...")

    def handleMessage(self, message: Message):
        if message.type == 'register':
            self.__handleRegister(message=message)
        elif message.type == 'data':
            self.__handleData(message=message)
        elif message.type == 'result':
            self.__handleResult(message=message)
        elif message.type == 'lookup':
            self.__handleLookup(message=message)
        elif message.type == 'ready':
            self.__handleReady(message=message)
        elif message.type == 'exit':
            self.__handleExit(message=message)
        elif message.type == 'profiler':
            self.__handleProfiler(message=message)

    def __handleRegister(self, message: Message):
        respond = self.registry.register(message=message)
        if respond is None:
            return self.__stopClient(
                message.source.addr,
                'No such role: %s' % message.content['role'])
        self.sendMessage(respond, message.source.addr)
        self.logger.info('%s registered', respond['nameLogPrinting'])

        if message.content['role'] == 'user':
            while self.registry.messageForWorker.qsize():
                msg, addr = self.registry.messageForWorker.get()
                self.sendMessage(msg, addr)

    def __handleData(self, message: Message):
        userID = message.content['userID']
        if userID not in self.registry.users:
            return self.__stopClient(
                message.source.addr,
                'User-%d does not exist' % userID)
        user = self.registry.users[userID]
        if not user.addr == message.source.addr:
            return self.__stopClient(
                message.source.addr,
                'You are not User-%d' % userID)

        for taskName in user.entranceTasksByName:
            taskHandlerToken = user.taskNameTokenMap[taskName].token
            taskHandler = self.registry.taskHandlerByToken[taskHandlerToken]
            self.sendMessage(message.content, taskHandler.addr)

    def __handleResult(self, message: Message):
        userID = message.content['userID']
        if userID not in self.registry.users:
            return self.__stopClient(
                message.source.addr,
                'User-%d does not exist' % userID)
        user = self.registry.users[userID]
        self.sendMessage(message.content, user.addr)

    def __handleLookup(self, message: Message):
        taskHandlerToken = message.content['token']
        if taskHandlerToken not in self.registry.taskHandlerByToken:
            return self.__stopClient(
                message.source.addr,
                'TaskHandler does not exist by token: %s' % taskHandlerToken)
        taskHandler = self.registry.taskHandlerByToken[taskHandlerToken]
        respond = {
            'type': 'taskHandlerInfo',
            'addr': taskHandler.addr,
            'token': taskHandlerToken
        }
        self.sendMessage(respond, message.source.addr)

    def __handleReady(self, message: Message):
        if not message.source.role == 'TaskHandler':
            return self.__stopClient(
                message.source.addr,
                'You are not TaskHandler')

        taskHandlerToken = message.content['token']
        taskHandler = self.registry.taskHandlerByToken[taskHandlerToken]
        taskHandler.ready.set()

        user = taskHandler.user
        user.lock.acquire()
        user.taskHandlerByTaskName[taskHandler.taskName] = taskHandler
        if len(user.taskNameTokenMap) == len(user.taskHandlerByTaskName):
            for taskName, taskHandler in user.taskHandlerByTaskName.items():
                if not taskHandler.ready.is_set():
                    user.lock.release()
                    return
            if not user.isReady:
                msg = {'type': 'ready'}
                self.sendMessage(msg, user.addr)
                user.isReady = True
        user.lock.release()

    def __handleExit(self, message: Message):
        self.logger.info(
            '%s at %s exit with reason: %s',
            message.source.nameLogPrinting,
            str(message.source.addr),
            message.content['reason'])
        if message.source.machineID not in self.registry.clients:
            return
        if message.source.role == 'user':
            user = self.registry.users[message.source.id]
            msg = {'type': 'stop', 'reason': 'Your User has exited.'}
            for taskHandler in user.taskHandlerByTaskName.values():
                self.sendMessage(msg, taskHandler.addr)
            del self.registry.users[message.source.id]
        elif message.source.role == 'TaskHandler':
            if message.source.id in self.registry.taskHandlers:
                taskHandler = self.registry.taskHandlers[message.source.id]
                del self.registry.taskHandlerByToken[taskHandler.token]
                del self.registry.taskHandlers[message.source.id]
        elif message.source.role == 'worker':
            del self.registry.workers[message.source.id]

        if message.source.machineID in self.registry.clients:
            del self.registry.clients[message.source.machineID]

    def __handleProfiler(self, message: Message):
        profilers = message.content['profiler']
        # Merge
        self.edges = {**self.edges, **profilers[0]}
        self.nodeResources = {**self.nodeResources, **profilers[1]}
        self.averageProcessTime = {**self.averageProcessTime, **profilers[2]}
        self.averageRespondTime = {**self.averageRespondTime, **profilers[3]}
        self.imagesAndRunningContainers = {**self.imagesAndRunningContainers, **profilers[4]}

        # update
        self.scheduler.edges = self.edges
        self.scheduler.averageProcessTime = self.averageProcessTime

    def __stopClient(self, addr: Address, reason: str = 'No reason'):
        msg = {'type': 'stop', 'reason': reason}
        self.sendMessage(msg, addr)

    def __requestProfiler(self):
        msg = {'type': 'requestProfiler'}
        self.sendMessage(msg, self.loggerAddr)


if __name__ == '__main__':
    myAddr_ = (sys.argv[1], int(sys.argv[2]))
    masterAddr_ = (sys.argv[3], int(sys.argv[4]))
    loggerAddr_ = (sys.argv[5], int(sys.argv[6]))
    master_ = Master(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_
    )
    master_.run()
