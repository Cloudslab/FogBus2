import logging
import argparse
from node import Node, Address
from connection import Message
from logger import get_logger
from profilerManage import Profiler
from connection import Median


class RemoteLogger(Profiler, Node):
    def __init__(
            self,
            containerName: str,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            logLevel=logging.DEBUG):
        Profiler.__init__(self)
        Node.__init__(
            self,
            role='RemoteLogger',
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            periodicTasks=[
                (self._saveToPersistentStorage, 2)],
            loggerAddr=loggerAddr,
            ignoreSocketErr=True)

        self.logLevel = logLevel

    def run(self):
        self.role = 'RemoteLogger'
        self.id = 0
        self.setName()
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.logger.info('Running ...')

    def handleMessage(self, message: Message):
        self.lock.acquire()
        if message.type == 'medianReceivedPackageSize':
            self.__handleMedianReceivedPackageSize(message=message)
        elif message.type == 'medianProcessTime':
            self.__handleMedianProcessTime(message=message)
        elif message.type == 'nodeResources':
            self.__handleNodeResources(message=message)
        elif message.type == 'taskHandlerResources':
            self.__handleTaskHandlerResources(message=message)
        elif message.type == 'respondTime':
            self.__handleResponseTime(message=message)
        elif message.type == 'delays':
            self.__handleDelays(message=message)
        elif message.type == 'imagesAndRunningContainers':
            self.__handleImagesAndRunningContainers(message=message)
        elif message.type == 'requestProfiler':
            self.__handleRequestProfiler(message=message)
        self.lock.release()

    def __handleMedianReceivedPackageSize(self, message: Message):
        source = message.source.name
        if source not in self.medianPackageSize:
            self.medianPackageSize[source] = {}
        for dest, medianReceivedPackageSize in message.content['medianReceivedPackageSize'].items():
            self.medianPackageSize[source][dest] = medianReceivedPackageSize

    def __handleDelays(self, message: Message):
        source = message.source.nameConsistent

        if source not in self.medianDelay:
            self.medianDelay[source] = {}

        sourceMachineID = message.source.machineID
        if sourceMachineID not in self._medianDelay:
            self._medianDelay[sourceMachineID] = {}
            self.medianDelay[sourceMachineID] = {}

        for dest, delay in message.content['delays'].items():
            self.medianDelay[source][dest] = delay
            destMachineID = dest[-64:]
            if destMachineID not in self._medianDelay[sourceMachineID]:
                self._medianDelay[sourceMachineID][destMachineID] = Median()
            self._medianDelay[sourceMachineID][destMachineID].update(delay)
            self.medianDelay[sourceMachineID][destMachineID] = self._medianDelay[sourceMachineID][
                destMachineID].median()

    def __handleNodeResources(self, message: Message):
        nodeName = message.source.nameConsistent
        nodeResources = message.content['resources']
        self.nodeResources[nodeName] = nodeResources

    def __handleTaskHandlerResources(self, message: Message):
        nodeName = message.content['nameConsistent']
        nodeResources = message.content['resources']
        self.nodeResources[nodeName] = nodeResources

    def __handleMedianProcessTime(self, message: Message):
        taskHandlerNameConsistent = message.source.nameConsistent
        taskHandlerName = message.source.name
        workerMachineID = message.source.machineID

        medianProcessTime = message.content['medianProcessTime']
        self.medianProcessTime[taskHandlerNameConsistent] = medianProcessTime
        self.medianProcessTime[taskHandlerName] = medianProcessTime

        if workerMachineID not in self._medianProcessTime:
            self._medianProcessTime[workerMachineID] = Median()
        self._medianProcessTime[workerMachineID].update(medianProcessTime[0])

    def __handleResponseTime(self, message: Message):
        userName = message.source.nameConsistent
        respondTime = message.content['respondTime']
        self.medianRespondTime[userName] = respondTime

    def __handleImagesAndRunningContainers(self, message: Message):
        workerName = message.source.nameConsistent
        workerInfo = message.content['imagesAndRunningContainers']
        self.imagesAndRunningContainers[workerName] = workerInfo

    def __handleRequestProfiler(self, message: Message):
        if not message.source.role == 'Master':
            return
        msg = {
            'type': 'profiler',
            'profiler': [
                self.medianPackageSize,
                self.medianDelay,
                self.nodeResources,
                self.medianProcessTime,
                self.medianRespondTime,
                self.imagesAndRunningContainers,
            ]}
        self.sendMessage(msg, message.source.addr)


def parseArg():
    parser = argparse.ArgumentParser(
        description='Remote Logger'
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
        help='Remote logger ip.'
    )
    parser.add_argument(
        'port',
        metavar='ListenPort',
        type=int,
        help='Remote logger port.'
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
        help='Master port (used for verifying master.)'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()
    remoteLogger_ = RemoteLogger(
        containerName=args.containerName,
        myAddr=(args.ip, args.port),
        masterAddr=(args.masterIP, args.masterPort),
        loggerAddr=(args.ip, args.port)
    )
    remoteLogger_.run()
