import logging
import argparse

from logger import get_logger
from registry import Registry
from connection import Message, Identity
from collections import defaultdict
from typing import Tuple, DefaultDict, Set
from datatype import TaskHandler
from ipaddress import ip_network
from time import sleep
from threading import Event
from iperf3 import Server as NetProfServer
from iperf3 import Client as NetProfClient
from pythonping import ping

Address = Tuple[str, int]


class Master(Registry):

    def __init__(
            self,
            containerName,
            myAddr,
            masterAddr,
            loggerAddr,
            initWithLog: bool,
            schedulerName: str,
            createdBy: str,
            minHosts: int,
            masterID: int = 0,
            netGateway: str = '',
            subnetMask: str = '255.255.255.0',
            logLevel=logging.DEBUG):
        Registry.__init__(
            self,
            createdBy=createdBy,
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            ignoreSocketErr=True,
            schedulerName=schedulerName,
            initWithLog=initWithLog,
            logLevel=logLevel,
            periodicTasks=[
                (self.__uploadBPS, 20),
                (self.__uploadPing, 20),
                (self.__getWorkerAddrFromOtherMasters, 300)],
        )
        self.id = masterID
        self.netGateway = netGateway
        self.subnetMask = subnetMask
        self.neighboursIP = None
        self.createdBy = createdBy
        self.minHosts: int = minHosts

        self.sysHosts: Set = set([])
        self.netTestPingEvent: DefaultDict[str, DefaultDict[str, Event]] = defaultdict(
            lambda: defaultdict(lambda: Event()))
        self.netTestBPSEvent: DefaultDict[str, DefaultDict[str, Event]] = defaultdict(
            lambda: defaultdict(lambda: Event()))
        self.netTest: Event = Event()

    def run(self):
        self.role = 'Master'
        self.setName()
        self.logger = get_logger(
            logger_name=self.nameLogPrinting,
            level_name=self.logLevel)
        self.logger.info("Serving ...")
        # if this Master was created by another
        if len(self.createdBy):
            # get the Workers' addr
            # and then advertise itself
            # A Master listens on a fixed port
            # TODO: make the port flexible
            self.logger.info('Created by %s' % self.createdBy)
            addr = (self.createdBy, 5000)
            self.__getWorkersAddrFrom(addr)
            self.__getProfiler(addr)
            self.netTest.set()
            return

        self.__netProfile()

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
        elif message.type == 'getProfiler':
            self.__handleGetProfiler(message=message)
        elif message.type == 'workersCount':
            self.__handleWorkersCount(message=message)
        elif message.type == 'nodeResources':
            self.__handleWorkerResources(message=message)
        elif message.type == 'schedulingResult':
            self.__handleSchedulingResult(message=message)
        elif message.type == 'waiting':
            self.__handleTaskHandlerWaiting(message=message)
        elif message.type == 'workersAddr':
            self.__handleWorkersAddr(message=message)
        elif message.type == 'workersAddrResult':
            self.__handleWorkersAddrResult(message=message)
        elif message.type == 'netTestReceive':
            self.__handleNetTestReceive(message=message)
        elif message.type == 'netTestSend':
            self.__handleNetTestSend(message=message)
        elif message.type == 'netTestResult':
            self.__handleNetTestResult(message=message)
        elif message.type == 'pingResult':
            self.__handlePingResult(message=message)

    def __handleRegister(self, message: Message):
        if message.content['role'] == 'User':
            self.netTest.wait()
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
            if taskHandlerToken not in self.taskHandlerByToken:
                continue
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
        if taskHandlerToken not in self.taskHandlerByToken:
            return
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
                self.logger.info('%s is ready to run. ' % user.nameLogPrinting)
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
                self.__askTaskHandlerToWait(taskHandler)
                # self.__stopClient(taskHandler, 'Your User has exited.')
            del self.users[message.source.id]
        elif message.source.role == 'TaskHandler':
            if message.source.id not in self.taskHandlers:
                return
            taskHandler = self.taskHandlers[message.source.id]
            if taskHandler.user.id in self.users:
                user = self.users[taskHandler.user.id]
                if taskHandler.taskName in \
                        taskHandler.user.taskHandlerByTaskName:
                    del taskHandler.user.taskHandlerByTaskName[taskHandler.taskName]
                # self.__stopClient(user, 'Your resources was released.')
            del self.taskHandlerByToken[taskHandler.token]
            del self.taskHandlers[message.source.id]
        elif message.source.role == 'Worker':
            if message.source.id not in self.workers:
                return
            del self.workers[message.source.id]
            del self.workers[message.source.machineID]
            del self.workers[message.source.addr[0]]
            self.workersCount -= 1

    def __handleGetProfiler(self, message: Message):
        msg = {
            'type': 'profiler',
            'profiler': [
                self.medianPackageSize,
                self.medianDelay,
                self.nodeResources,
                self.medianProcessTime,
                self.medianRespondTime,
                self.imagesAndRunningContainers,
                self.bps,
                self.ping
            ]
        }
        self.sendMessage(msg, message.source.addr)

    def __handleProfiler(self, message: Message):
        profilers = message.content['profiler']
        # Merge

        self.nodeResources = {**self.nodeResources, **profilers[2]}
        self.medianProcessTime = {**self.medianProcessTime, **profilers[3]}
        self.medianRespondTime = {**self.medianRespondTime, **profilers[4]}
        self.imagesAndRunningContainers = {**self.imagesAndRunningContainers, **profilers[5]}

        for sourceMachineID, dests in profilers[0].items():
            if sourceMachineID not in self.medianPackageSize:
                self.medianPackageSize[sourceMachineID] = {}
            for destMachineID, value in dests.items():
                self.medianPackageSize[sourceMachineID][destMachineID] = value

        for sourceMachineID, dests in profilers[1].items():
            if sourceMachineID not in self.medianDelay:
                self.medianDelay[sourceMachineID] = {}
            for destMachineID, value in dests.items():
                self.medianDelay[sourceMachineID][destMachineID] = value

        for sourceMachineID, dests in profilers[6].items():
            if sourceMachineID not in self.bps:
                self.bps[sourceMachineID] = {}
            for destMachineID, value in dests.items():
                self.bps[sourceMachineID][destMachineID] = value

        for sourceMachineID, dests in profilers[7].items():
            if sourceMachineID not in self.ping:
                self.ping[sourceMachineID] = {}
            for destMachineID, value in dests.items():
                self.ping[sourceMachineID][destMachineID] = value

        # update
        self.scheduler.medianPackageSize = self.medianPackageSize
        self.scheduler.medianDelay = self.medianDelay
        self.scheduler.medianProcessTime = self.medianProcessTime
        self.scheduler.bps = self.bps
        self.scheduler.ping = self.ping

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

    def __handleSchedulingResult(self, message: Message):
        userID = message.content['userID']
        decision = message.content['decision']
        lockName = 'schedulingUser-%d' % userID
        self.decisionResultFromWorker[lockName] = decision
        self.locks[lockName].release()
        self.logger.info('Received decision from %s' % message.source.nameLogPrinting)

    def __handleTaskHandlerWaiting(self, message: Message):
        if message.source.id not in self.taskHandlers:
            return
        taskHandler = self.taskHandlers[message.source.id]
        self.makeTaskHandlerWait(taskHandler)

    def __handleWorkersAddr(self, message: Message):
        """
        :param message:
        :return: Workers' addr registered here
        """

        workersAddr = self.__getWorkersAddr()
        if not len(workersAddr):
            return
        msg = {
            'type': 'workersAddrResult',
            'workersAddrResult': workersAddr
        }
        self.sendMessage(msg, message.source.addr)

    def __handleWorkersAddrResult(self, message: Message):
        """
        Handle Workers' Addr from another Master
        :param message:
        :return:
        """
        workersAddr = message.content['workersAddrResult']

        # self.logger.info('Got Workers\' addrs from %s' % str(message.source.addr))
        # self.logger.info(workersAddr)
        self.__advertiseSelfToWorkers(workersAddr)

    def __advertiseSelfToWorkers(self, workersAddr: set[Address]):
        """
        Advertise myself to Workers that registered at another Master
        :param workersAddr:
        :return:
        """
        myWorkersAddr = self.__getWorkersAddr()
        if not len(workersAddr):
            return
        myWorkersSet = set([addr[0] for addr in myWorkersAddr])
        msg = {'type': 'advertise'}
        for workerAddr in workersAddr:
            if workerAddr[0] in myWorkersSet:
                continue
            self.sendMessage(msg, workerAddr)

    def __getWorkersAddr(self):
        """
        :return: Workers' addr info
        """
        workersAddr = set([])
        for worker in self.workers.values():
            if worker.addr in workersAddr:
                continue
            workersAddr.add(worker.addr)
        return workersAddr

    def __getWorkerAddrFromOtherMasters(self):
        """
        Get Workers' addr from neighbours in the network
        :return:
        """
        if self.neighboursIP is None:
            self.neighboursIP = self.__generateNeighboursIP()
        for ip in self.neighboursIP:
            addr = (str(ip), 5000)
            if addr == self.addr:
                continue
            self.__getWorkersAddrFrom(addr)
            sleep(1)

    def __getWorkersAddrFrom(self, addr: Address):
        """
        Get Workers' info from the addr
        :param addr:
        :return:
        """
        msg = {'type': 'workersAddr'}
        self.sendMessage(msg, addr)

    def __getProfiler(self, addr: Address):
        msg = {'type': 'getProfiler'}
        self.sendMessage(msg, addr)

    def __generateNeighboursIP(self):
        """
        Generate neighbours' IP using subnetwork mask
        :return:
        """
        selfIP = self.addr[0]
        if self.netGateway == '':
            self.netGateway = selfIP[:selfIP.rfind('.')] + '.0'
        network = ip_network('%s/%s' % (self.netGateway, self.subnetMask))
        return network

    def __askTaskHandlerToWait(self, taskHandler: TaskHandler):
        msg = {'type': 'wait'}
        self.sendMessage(msg, taskHandler.addr)

    def __stopClient(self, identity: Identity, reason: str = 'No reason'):
        msg = {'type': 'stop', 'reason': reason}
        self.sendMessage(msg, identity.addr)

    def __netProfile(self):
        minHosts = self.minHosts
        self.logger.info('Waiting for %d hosts', self.minHosts)
        while len(self.sysHosts) < minHosts:
            self.sysHosts = self.__getHosts()
            sleep(1)
        self.logger.info('%d workers connected, begin network profiling', self.minHosts)
        for sourceMachineID in self.sysHosts:
            for targetMachineID in self.sysHosts:
                if targetMachineID == sourceMachineID:
                    continue
                if sourceMachineID in self.bps \
                        and targetMachineID in self.bps[sourceMachineID]:
                    continue
                self.__runNetTest(sourceMachineID, targetMachineID)
                self.netTestPingEvent[sourceMachineID][targetMachineID].wait()
                self.netTestBPSEvent[sourceMachineID][targetMachineID].wait()
                # del self.netTestPingEvent[sourceMachineID][targetMachineID]
                # del self.netTestBPSEvent[sourceMachineID][targetMachineID]
        self.netTest.set()
        self.logger.info('Finished Net Test')

    def __getHosts(self):
        hosts = {self.machineID}
        for worker in self.workers.values():
            if worker.machineID in hosts:
                continue
            hosts.add(worker.machineID)
        return hosts

    def __runNetTest(self, sourceMachineID: str, targetMachineID: str):
        if sourceMachineID == self.machineID:
            sourceAddr = self.myAddr
        else:
            sourceAddr = self.workers[sourceMachineID].addr

        if targetMachineID == self.machineID:
            targetAddr = self.myAddr
        else:
            targetAddr = self.workers[targetMachineID].addr

        msg = {
            'type': 'netTestReceive',
            'sourceAddr': sourceAddr,
            'sourceMachineID': sourceMachineID
        }
        self.logger.info(
            'Waiting for net profile from %s to %s',
            sourceAddr[0],
            targetAddr[0]
        )
        # while not self.netTestBPSEvent[sourceMachineID][targetMachineID].isSet() \
        #         or not self.netTestPingEvent[sourceMachineID][targetMachineID].isSet():
        self.sendMessage(msg, targetAddr)
        # sleep(5)

    def __handleNetTestReceive(self, message: Message):
        sourceAddr = message.content['sourceAddr']
        sourceMachineID = message.content['sourceMachineID']
        msg = {
            'type': 'netTestSend',
            'targetMachineID': self.machineID
        }
        self.sendMessage(msg, sourceAddr)
        self.logger.info(
            'Running net profiling from %s to %s as target',
            sourceAddr[0],
            self.myAddr[0]
        )
        self.__runNetTestReceive(sourceMachineID)

    def __runNetTestReceive(
            self,
            sourceMachineID: str):
        server = NetProfServer()
        server.bind_address = self.addr[0]
        server.port = 10000
        while True:
            try:
                bps = server.run().received_bps
                break
            except (AttributeError, IndexError):
                self.logger.warning(
                    'Retry receiving',
                )
                sleep(1)
                continue
        msg = {'type': 'netTestResult',
               'sourceMachineID': sourceMachineID,
               'targetMachineID': self.machineID,
               'bps': bps}
        self.sendMessage(msg, self.masterAddr)

        self.logger.info(
            'Uploaded net profiling log from %s to %s ',
            sourceMachineID[:7],
            self.machineID[:7]
        )

    def __handleNetTestSend(self, message: Message):
        client = NetProfClient()
        client.bind_address = self.myAddr[0]
        client.server_hostname = message.source.addr[0]
        client.port = 10000
        while True:
            try:
                # client.run()
                res = client.run().sent_bps
                print(res)
                break
            except (AttributeError, IndexError):
                self.logger.warning(
                    'Retry connecting %s',
                    message.source.addr[0]
                )
                sleep(1)
                continue
        self.logger.info(
            'Done net profiling from %s to %s as source',
            self.myAddr[0],
            message.source.addr[0]
        )
        for i in range(5):
            pingResponseList = ping(message.source.addr[0], size=40, count=10)
            pingResult = pingResponseList.rtt_avg_ms

            msg = {
                'type': 'pingResult',
                'sourceMachineID': self.machineID,
                'targetMachineID': message.content['targetMachineID'],
                'pingResult': pingResult
            }
            self.sendMessage(msg, self.masterAddr)
            self.logger.info(
                'Uploaded ping from %s to %s',
                self.myAddr[0],
                message.source.addr[0]
            )

    def __handleNetTestResult(self, message: Message):
        sourceMachineID = message.content['sourceMachineID']
        targetMachineID = message.content['targetMachineID']
        bps = message.content['bps']
        if sourceMachineID not in self.bps:
            self.bps[sourceMachineID] = {}
        self.bps[sourceMachineID][targetMachineID] = bps
        self.netTestBPSEvent[sourceMachineID][targetMachineID].set()
        self.logger.info(
            'Received BPS result from %s to %s',
            sourceMachineID[:7],
            targetMachineID[:7]
        )

    def __handlePingResult(self, message: Message):
        sourceMachineID = message.content['sourceMachineID']
        targetMachineID = message.content['targetMachineID']
        pingResult = message.content['pingResult']

        if sourceMachineID not in self.ping:
            self.ping[sourceMachineID] = {}
        self.ping[sourceMachineID][targetMachineID] = pingResult
        self.netTestPingEvent[sourceMachineID][targetMachineID].set()
        self.logger.info(
            'Received Ping result from %s to %s',
            sourceMachineID[:7],
            targetMachineID[:7]
        )

    def __uploadBPS(self):
        msg = {'type': 'bps', 'bps': self.bps}
        self.sendMessage(msg, self.remoteLogger.addr)

    def __uploadPing(self):
        msg = {'type': 'ping', 'ping': self.ping}
        self.sendMessage(msg, self.remoteLogger.addr)


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

    parser.add_argument(
        'createdBy',
        metavar='CreatedBy',
        nargs='?',
        default='',
        type=str,
        help='IP of the Master who asked to create this new Master'
    )

    parser.add_argument(
        '--minHosts',
        metavar='MinHosts',
        default=1,
        type=int,
        help='minimum hosts needed'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()
    containerName_ = args.containerName
    master_ = Master(
        containerName=containerName_,
        myAddr=(args.ip, args.port),
        masterAddr=(args.ip, args.port),
        loggerAddr=(args.loggerIP, args.loggerPort),
        schedulerName=args.schedulerName,
        initWithLog=True if args.initWithLog else False,
        createdBy=args.createdBy,
        minHosts=args.minHosts
    )
    master_.run()
