import logging
import threading
import os
import re
import docker
import argparse
import psutil
from exceptions import *
from connection import Message
from node import Node, ImagesAndContainers
from logger import get_logger
from gatherContainerStat import GatherContainerStat
from queue import Queue
from time import time
from scheduling import NSGA2, NSGA3
from traceback import print_exc
from networkProfilter import NetProfiler


class Worker(Node, GatherContainerStat):

    def __init__(
            self,
            containerName,
            myAddr,
            masterAddr,
            loggerAddr,
            logLevel=logging.DEBUG):

        self.isRegistered: threading.Event = threading.Event()
        self.dockerClient = docker.from_env()
        self.currPath = os.path.abspath(os.path.curdir)
        Node.__init__(
            self,
            role='Worker',
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadImagesAndRunningContainersList, 10),
                (self.__uploadResources, 20),
                (self.__uploadTaskHandlerResources, 20)],
            logLevel=logLevel
        )
        self.containerStats = Queue()
        GatherContainerStat.__init__(
            self,
            self.dockerClient)
        self.taskHandlers = {}
        self.totalCPUCores = 0
        self.cpuFreq = .0
        self.resources = None
        self.netProfiler: NetProfiler = NetProfiler()

    def run(self):
        self.__register()
        self._runContainerStat()

    def __register(self):
        self.logger.info('Getting local available images ...')
        resources = self._getResources()
        self.totalCPUCores = resources['totalCPUCores']
        self.cpuFreq = resources['cpuFreq']
        message = {'type': 'register',
                   'role': 'Worker',
                   'machineID': self.machineID,
                   'resources': resources,
                   'images': self.__getImages()}
        self.sendMessage(message, self.master.addr)
        self.isRegistered.wait()
        self.logger.info("Registered.")

    def handleMessage(self, message: Message):
        if self.isMessage(message, 'registered'):
            self.__handleRegistered(message)
        elif self.isMessage(message, 'runTaskHandler'):
            self.__handleRunTaskHandler(message)
        elif message.type == 'resourcesQuery':
            self.__handleResourcesQuery(message)
        elif message.type == 'scheduling':
            self.__handleScheduling(message)
        elif message.type == 'createMaster':
            self.__handleCreateMaster(message)
        elif message.type == 'advertise':
            self.__handleAdvertise(message)
        elif message.type == 'netTestReceive':
            self.__handleNetTestReceive(message=message)
        elif message.type == 'netTestSend':
            self.__handleNetTestSend(message=message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'Worker':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.role = role
        self.setName(message)
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.isRegistered.set()

    def __handleResourcesQuery(self, message: Message):
        if not self.role == 'Worker':
            return
        if not message.source.addr == self.masterAddr:
            return
        resources = self._getResources()
        msg = {
            'type': 'nodeResources',
            'resources': resources}
        self.sendMessage(msg, message.source.addr)

    def __handleRunTaskHandler(self, message: Message):
        userID = message.content['userID']
        userName = message.content['userName']
        taskName = message.content['taskName']
        token = message.content['token']
        childTaskTokens = message.content['childTaskTokens']
        workerID = self.id
        totalCPUCores = self.totalCPUCores
        cpuFreq = self.cpuFreq
        try:
            containerName = '%s_%s_%s_%s' % (
                taskName,
                userName.replace('@', ''),
                self.nameLogPrinting,
                time())
            # for container in self.dockerClient.containers.list():
            #     if container.name != containerName:
            #         continue
            #     container.stop()
            #     break
            command = '%s %s %s %d %s %d ' \
                      '%d %s %s %s %s %d ' \
                      '%d %s' % (
                          containerName,
                          self.myAddr[0],
                          self.masterAddr[0],
                          self.masterAddr[1],
                          self.loggerAddr[0],
                          self.loggerAddr[1],
                          userID,
                          userName,
                          taskName,
                          token,
                          ','.join(childTaskTokens) if len(childTaskTokens) else 'None',
                          workerID,
                          totalCPUCores,
                          cpuFreq
                      )
            # self.logger.info(command)
            self.dockerClient.containers.run(
                name=containerName,
                detach=True,
                auto_remove=True,
                image=self.camel_to_snake(taskName),
                network_mode='host',
                working_dir='/workplace',
                command=command)
            self.taskHandlers[containerName] = '%s#%s' % (taskName, self.machineID)
            self.logger.info('Ran %s: %s', taskName, containerName)
        except docker.errors.APIError as e:
            self.logger.warning(str(e))

    def __handleScheduling(self, message: Message):
        self.logger.info('Handling scheduling task ...')
        schedulerName = message.content['schedulerName']
        medianDelay = message.content['medianDelay']
        medianProcessTime = message.content['medianProcessTime']
        populationSize = message.content['populationSize']
        generationNum = message.content['generationNum']
        userID = message.content['userID']
        userName = message.content['userName']
        userMachine = message.content['userMachine']
        userAppName = message.content['userAppName']
        userLabel = message.content['userLabel']
        masterName = message.content['masterName']
        masterMachine = message.content['masterMachine']
        availableWorkers = message.content['availableWorkers']
        machinesIndex = message.content['machinesIndex']

        self.logger.info(populationSize)
        self.logger.info(generationNum)
        if schedulerName == 'NSGA2':
            scheduler = NSGA2(
                medianDelay=medianDelay,
                medianProcessTime=medianProcessTime,
                populationSize=populationSize,
                generationNum=generationNum)
        elif schedulerName == 'NSGA3':
            scheduler = NSGA3(
                medianDelay=medianDelay,
                medianProcessTime=medianProcessTime,
                populationSize=populationSize,
                generationNum=generationNum,
                dasDennisP=1)
        else:
            return
        decision = scheduler.schedule(
            userName=userName,
            userMachine=userMachine,
            masterName=masterName,
            masterMachine=masterMachine,
            applicationName=userAppName,
            label=userLabel,
            availableWorkers=availableWorkers,
            machinesIndex=machinesIndex
        )

        self.logger.info(decision.machinesIndex)
        self.logger.info(decision.cost)
        msg = {
            'type': 'schedulingResult',
            'userID': userID,
            'decision': decision}
        self.sendMessage(msg, message.source.addr)
        self.logger.info('Sent decision to master.')

    def __handleCreateMaster(self, message: Message):
        loggerIP, loggerPort = message.content['loggerAddr']
        schedulerName = message.content['schedulerName']
        initWithLog = message.content['initWithLog']
        # try to create a Master
        try:
            command = 'Master ' \
                      '%s 5000 ' \
                      '%s %d ' \
                      '%s ' \
                      '%s ' \
                      '--initWithLog %s ' % (
                          self.addr[0],
                          loggerIP,
                          loggerPort,
                          schedulerName,
                          message.source.addr[0],
                          initWithLog)
            self.dockerClient.containers.run(
                name='Master',
                detach=True,
                auto_remove=True,
                image='master',
                network_mode='host',
                working_dir='/workplace',
                volumes={
                    '/var/run/docker.sock':
                        {
                            'bind': '/var/run/docker.sock',
                            'mode': 'rw'
                        }
                },
                command=command)
        except Exception:
            pass

    def __handleAdvertise(self, message: Message):
        if not self.__shouldCreateWorker():
            self.logger.info(
                'Decided not to create another worker for '
                '%s' % str(message.source.addr))
            return

        self.logger.info(
            'Decided to create another worker for '
            '%s' % str(message.source.addr))
        self.__createWorker(message)

    def __handleNetTestReceive(self, message: Message):
        sourceAddr = message.content['sourceAddr']
        sourceMachineID = message.content['sourceMachineID']
        msg = {'type': 'netTestSend'}
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
        result = self.netProfiler.receive()
        msg = {'type': 'netTestResult',
               'sourceMachineID': sourceMachineID,
               'targetMachineID': self.machineID,
               'bps': result}
        self.sendMessage(msg, self.masterAddr)
        self.logger.info(
            'Uploaded net profiling log from %s to %s ',
            sourceMachineID[:7],
            self.machineID[:7]
        )

    def __handleNetTestSend(self, message: Message):
        receiverAddr = (message.source.addr[0], 10000)
        while True:
            try:
                self.netProfiler.send(serverAddr=receiverAddr)
                break
            except AttributeError:
                sleep(1)
                continue
        self.logger.info(
            'Done net profiling from %s to %s as source',
            self.myAddr[0],
            receiverAddr[0]
        )

    @staticmethod
    def __shouldCreateWorker():
        cpuPercent = psutil.cpu_percent()
        memPercent = psutil.virtual_memory().percent
        print(cpuPercent, memPercent)
        if cpuPercent > 80 or memPercent > 80:
            return False

        return True

    def __createWorker(self, message: Message):

        try:
            newWorkerName = 'Worker-%f' % time()
            command = '%s ' \
                      '%s ' \
                      '%s %d ' \
                      '%s %d ' % (
                          newWorkerName,
                          self.addr[0],
                          message.source.addr[0],
                          message.source.addr[1],
                          self.loggerAddr[0],
                          self.loggerAddr[1],)
            self.dockerClient.containers.run(
                name=newWorkerName,
                detach=True,
                auto_remove=True,
                image='worker',
                network_mode='host',
                working_dir='/workplace',
                volumes={
                    '/var/run/docker.sock':
                        {
                            'bind': '/var/run/docker.sock',
                            'mode': 'rw'
                        }
                },
                command=command)
        except Exception:
            print_exc()

    @staticmethod
    def snake_to_camel(snake_str):
        if snake_str == 'oct':
            return 'OCR'
        # https://stackoverflow.com/questions/19053707
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)

    @staticmethod
    def camel_to_snake(name):
        # https://stackoverflow.com/questions/1175208
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def __getImages(self):
        return set([])
        imagesList = self.dockerClient.images.list()

        imageNames = set()
        for image in imagesList:
            tags = image.tags
            if not len(tags):
                continue
            imageNames.add(self.snake_to_camel(tags[0].split(':')[0]))
        return imageNames

    def __getContainers(self):
        containerList = self.dockerClient.containers.list()

        runningContainers = set()
        for container in containerList:
            tags = container.image.tags
            if not len(tags):
                continue
            runningContainers.add(self.snake_to_camel(tags[0].split(':')[0]))
        return runningContainers

    @staticmethod
    def _getCPUFreq():
        totalCoresCount = psutil.cpu_count(logical=True)
        cpuFreq = psutil.cpu_freq()
        # psutil.cpu_freq().current is dynamic
        # use max to run the experiment
        # for better scheduling
        currFreq = cpuFreq.max
        resCPU = totalCoresCount, currFreq
        return resCPU

    def _getResources(self):
        stats = self.container.stats(
            stream=False)
        cpuUsage = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        systemCPUUsage = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        if len(stats['memory_stats']):
            memoryUsage = stats['memory_stats']['usage']
            peekMemoryUsage = stats['memory_stats']['max_usage']
            maxMemory = stats['memory_stats']['limit']
        else:
            memoryUsage = 1
            peekMemoryUsage = 1
            maxMemory = 1
        totalCPUCores, cpuFreq = self._getCPUFreq()
        resources = {
            'systemCPUUsage': systemCPUUsage,
            'cpuUsage': cpuUsage,
            'memoryUsage': memoryUsage,
            'peekMemoryUsage': peekMemoryUsage,
            'maxMemory': maxMemory,
            'totalCPUCores': totalCPUCores,
            'cpuFreq': cpuFreq}
        self.resources = resources
        return resources

    def __uploadResources(self):
        resources = self._getResources()
        msg = {
            'type': 'nodeResources',
            'resources': resources}
        self.sendMessage(msg, self.remoteLogger.addr)
        self.sendMessage(msg, self.master.addr)

    def __uploadTaskHandlerResources(self):
        while True:
            if self._containerStats.qsize() == 0:
                break
            name, resources = self._containerStats.get()
            if name not in self.taskHandlers:
                continue
            nameConsistent = self.taskHandlers[name]
            msg = {
                'type': 'taskHandlerResources',
                'nameConsistent': nameConsistent,
                'resources': resources}
            self.sendMessage(msg, self.remoteLogger.addr)

    def __uploadImagesAndRunningContainersList(self):
        try:
            imagesAndContainers = ImagesAndContainers(
                images=self.__getImages(),
                containers=self.__getContainers())
            msg = {
                'type': 'imagesAndRunningContainers',
                'imagesAndRunningContainers': imagesAndContainers}
            self.sendMessage(msg, self.remoteLogger.addr)
        except Exception as e:
            self.logger.warning(str(e))


def parseArg():
    parser = argparse.ArgumentParser(
        description='User'
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
        help='User ip.'
    )
    parser.add_argument(
        'masterIP',
        metavar='MasterIP',
        type=str,
        help='Master ip.'
    )
    parser.add_argument(
        'masterPort',
        metavar='MasterPort',
        type=int,
        help='Master port'
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
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()
    worker_ = Worker(
        containerName=args.containerName,
        myAddr=(args.ip, 0),
        masterAddr=(args.masterIP, args.masterPort),
        loggerAddr=(args.loggerIP, args.loggerPort), )
    worker_.run()
