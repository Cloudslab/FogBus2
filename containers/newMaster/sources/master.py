import logging
import argparse
from logger import get_logger
from registry import Registry
from connection import Message, Identity
from typing import Tuple

Address = Tuple[str, int]


class Master(Registry):

    def __init__(
            self,
            containerName,
            myAddr,
            masterAddr,
            loggerAddr,
            schedulerName: str,
            masterID: int = 0,
            initWithLog: bool = False,
            logLevel=logging.DEBUG):
        Registry.__init__(
            self,
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            ignoreSocketErr=True,
            schedulerName=schedulerName,
            initWithLog=initWithLog,
            logLevel=logLevel)
        self.id = masterID

    def run(self):
        self.role = 'Master'
        self.setName()
        self.logger = get_logger(
            logger_name=self.nameLogPrinting,
            level_name=self.logLevel)
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
        elif message.type == 'workersCount':
            self.__handleWorkersCount(message=message)
        elif message.type == 'nodeResources':
            self.__handleWorkerResources(message=message)

    def __handleRegister(self, message: Message):
        respond = self.registerClient(message=message)
        if respond is None:
            self.__stopClient(
                message.source, 'Unknown Err')
            return
        self.sendMessage(respond, message.source.addr)
        if respond['type'] == 'registered' \
                and respond['role'] != 'TaskHandler':
            self.logger.info('%s registered', respond['nameLogPrinting'])

    def __handleData(self, message: Message):
        userID = message.content['userID']
        if userID not in self.users:
            return self.__stopClient(
                message.source,
                'User-%d does not exist' % userID)
        user = self.users[userID]
        if not user.addr == message.source.addr:
            return self.__stopClient(
                message.source,
                'You are not User-%d' % userID)

        for taskName in user.entranceTasksByName:
            taskHandlerToken = user.taskNameTokenMap[taskName].token
            taskHandler = self.taskHandlerByToken[taskHandlerToken]
            self.sendMessage(message.content, taskHandler.addr)

    def __handleResult(self, message: Message):
        userID = message.content['userID']
        if userID not in self.users:
            return self.__stopClient(
                message.source,
                'User-%d does not exist' % userID)
        user = self.users[userID]
        self.sendMessage(message.content, user.addr)

    def __handleLookup(self, message: Message):
        taskHandlerToken = message.content['token']
        if taskHandlerToken not in self.taskHandlerByToken:
            return
        taskHandler = self.taskHandlerByToken[taskHandlerToken]
        respond = {
            'type': 'taskHandlerInfo',
            'addr': taskHandler.addr,
            'token': taskHandlerToken
        }
        self.sendMessage(respond, message.source.addr)

    def __handleReady(self, message: Message):
        if not message.source.role == 'TaskHandler':
            return self.__stopClient(
                message.source,
                'You are not TaskHandler')

        taskHandlerToken = message.content['token']
        taskHandler = self.taskHandlerByToken[taskHandlerToken]
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
        if message.content['reason'] != 'Manually interrupted.':
            self.logger.info(
                '%s at %s exit with reason: %s',
                message.source.nameLogPrinting,
                str(message.source.addr),
                message.content['reason'])

        self.__stopClient(
            message.source,
            'Your asked for. Reason: %s' % message.content['reason'])

        if message.source.role == 'User':
            if message.source.id not in self.users:
                return
            user = self.users[message.source.id]
            for taskHandler in user.taskHandlerByTaskName.values():
                self.__stopClient(taskHandler, 'Your User has exited.')
            del self.users[message.source.id]
        elif message.source.role == 'TaskHandler':
            if message.source.id not in self.taskHandlers:
                return
            taskHandler = self.taskHandlers[message.source.id]
            if taskHandler.user.id in self.users:
                user = self.users[taskHandler.user.id]
                del taskHandler.user.taskHandlerByTaskName[taskHandler.taskName]
                self.__stopClient(user, 'Your resources was released.')
            del self.taskHandlerByToken[taskHandler.token]
            del self.taskHandlers[message.source.id]
        elif message.source.role == 'Worker':
            if message.source.id not in self.workers:
                return
            del self.workers[message.source.id]
            del self.workers[message.source.machineID]
            self.workersCount -= 1

    def __handleProfiler(self, message: Message):
        profilers = message.content['profiler']
        # Merge
        self.medianPackageSize = {**self.medianPackageSize, **profilers[0]}
        self.medianDelay = {**self.medianDelay, **profilers[1]}
        self.nodeResources = {**self.nodeResources, **profilers[2]}
        self.medianProcessTime = {**self.medianProcessTime, **profilers[3]}
        self.medianRespondTime = {**self.medianRespondTime, **profilers[4]}
        self.imagesAndRunningContainers = {**self.imagesAndRunningContainers, **profilers[5]}

        # update
        self.scheduler.medianPackageSize = self.medianPackageSize
        self.scheduler.medianDelay = self.medianDelay
        self.scheduler.medianProcessTime = self.medianProcessTime

    def __handleWorkersCount(self, message: Message):
        msg = {'type': 'workersCount', 'workersCount': self.workersCount}
        self.sendMessage(msg, message.source.addr)

    def __handleWorkerResources(self, message: Message):
        if message.source.nameConsistent not in self.workers:
            return
        worker = self.workers[message.source.nameConsistent]
        resources = message.content['resources']
        worker.cpuUsage = resources['cpuUsage']
        worker.systemCPUUsage = resources['systemCPUUsage']
        worker.memoryUsage = resources['memoryUsage']
        worker.peekMemoryUsage = resources['peekMemoryUsage']
        worker.maxMemory = resources['maxMemory']
        worker.totalCPUCores = resources['totalCPUCores']
        worker.cpuFreq = resources['cpuFreq']

    def __stopClient(self, identity: Identity, reason: str = 'No reason'):
        msg = {'type': 'stop', 'reason': reason}
        self.sendMessage(msg, identity.addr)


def parseArg():
    parser = argparse.ArgumentParser(
        description='Master'
    )
    parser.add_argument(
        'containerName',
        metavar='ContainerName',
        type=str,
        help='Current container name, used for getting runtime usages.'
    )
    parser.add_argument(
        'ip',
        metavar='BindIP',
        type=str,
        help='Master ip.'
    )
    parser.add_argument(
        'port',
        metavar='ListenPort',
        type=int,
        help='Master port.'
    )
    parser.add_argument(
        'loggerIP',
        metavar='RemoteLoggerIP',
        type=str,
        help='Remote logger ip.'
    )
    parser.add_argument(
        'loggerPort',
        metavar='RemoteLoggerPort',
        type=int,
        help='Remote logger port'
    )
    parser.add_argument(
        'schedulerName',
        metavar='SchedulerName',
        type=str,
        help='Scheduler name.'
    )

    parser.add_argument(
        '--initWithLog',
        metavar='InitWithLog',
        nargs='?',
        default=False,
        type=bool,
        help='True or False'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()
    containerName_ = args.containerName
    print(args.initWithLog)
    master_ = Master(
        containerName=containerName_,
        myAddr=(args.ip, args.port),
        masterAddr=(args.ip, args.port),
        loggerAddr=(args.loggerIP, args.loggerPort),
        schedulerName=args.schedulerName,
        initWithLog=True if args.initWithLog else False)
    master_.run()
