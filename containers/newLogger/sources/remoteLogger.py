import sys
import logging
from node import Node, Address
from connection import Message
from logger import get_logger
from profilerManage import Profiler


class RemoteLogger(Profiler, Node):
    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            logLevel=logging.DEBUG):
        Profiler.__init__(self)
        Node.__init__(
            self,
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
        if message.type == 'averageReceivedPackageSize':
            self.__handleAverageReceivedPackageSize(message=message)
        elif message.type == 'averageProcessTime':
            self.__handleAverageProcessTime(message=message)
        elif message.type == 'nodeResources':
            self.__handleNodeResources(message=message)
        elif message.type == 'respondTime':
            self.__handleResponseTime(message=message)
        elif message.type == 'delays':
            self.__handleDelays(message=message)
        elif message.type == 'imagesAndRunningContainers':
            self.__handleImagesAndRunningContainers(message=message)
        elif message.type == 'requestProfiler':
            self.__handleRequestProfiler(message=message)
        self.lock.release()

    def __handleAverageReceivedPackageSize(self, message: Message):
        source = message.source.name
        if source not in self.averagePackageSize:
            self.averagePackageSize[source] = {}
        for dest, averageReceivedPackageSize in message.content['averageReceivedPackageSize'].items():
            self.averagePackageSize[source][dest] = averageReceivedPackageSize

    def __handleDelays(self, message: Message):
        source = message.source.machineID
        if source not in self.averageDelay:
            self.averageDelay[source] = {}
        for dest, delay in message.content['delays'].items():
            self.averageDelay[source][dest] = delay

    def __handleNodeResources(self, message: Message):
        nodeName = message.source.nameConsistent
        nodeResources = message.content['resources']
        self.nodeResources[nodeName] = nodeResources

    def __handleAverageProcessTime(self, message: Message):
        workerName = message.source.nameConsistent
        averageProcessTime = message.content['averageProcessTime']
        self.averageProcessTime[workerName] = averageProcessTime

    def __handleResponseTime(self, message: Message):
        userName = message.source.nameConsistent
        respondTime = message.content['respondTime']
        self.averageRespondTime[userName] = respondTime

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
                self.averagePackageSize,
                self.averageDelay,
                self.nodeResources,
                self.averageProcessTime,
                self.averageRespondTime,
                self.imagesAndRunningContainers,
            ]}
        self.sendMessage(msg, message.source.addr)


if __name__ == '__main__':
    myAddr_ = (sys.argv[1], int(sys.argv[2]))
    masterAddr_ = (sys.argv[3], int(sys.argv[4]))
    loggerAddr_ = (sys.argv[5], int(sys.argv[6]))
    remoteLogger_ = RemoteLogger(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_
    )
    remoteLogger_.run()
