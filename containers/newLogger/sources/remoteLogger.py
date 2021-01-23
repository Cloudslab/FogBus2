import sys
import logging
import json
from node import Node, Address
from connection import Message, Average
from logger import get_logger
from edge import Edge
from typing import Dict, List, Tuple
from resourcesInfo import ResourcesInfo, WorkerInfo
from persistentStorage import PersistentStorage


class RemoteLogger(Node):
    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            logLevel=logging.DEBUG):

        self.edges: Dict[str, Edge] = {}
        self.nodeResources: Dict[str, ResourcesInfo] = {}
        self.averageProcessTime: Dict[str, float] = {}
        self.averageRespondTime: Dict[str, float] = {}
        self.imagesAndRunningContainers: Dict[str, WorkerInfo] = {}

        self.persistentStorage: PersistentStorage = PersistentStorage()
        self.__readFromPersistentStorage()

        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            periodicTasks=[
                (self.__saveToPersistentStorage, 2)],
            loggerAddr=loggerAddr)
        self.logLevel = logLevel

    def run(self):
        self.role = 'remoteLogger'
        self.id = 0
        self.name = '%s-%d' % (self.role, self.id)
        self.logger = get_logger(self.name, self.logLevel)
        self.logger.info('Running ...')

    def handleMessage(self, message: Message):
        if message.type == 'averageReceivedPackageSize':
            self.__handleAverageReceivedPackageSize(message=message)
        elif message.type == 'averageProcessTime':
            self.__handleAverageProcessTime(message=message)
        elif message.type == 'nodeResources':
            self.__handleNodeResources(message=message)
        elif message.type == 'respondTime':
            self.__handleResponseTime(message=message)
        elif message.type == 'roundTripDelay':
            self.__handleRoundTripDelay(message=message)
        elif message.type == 'imagesAndRunningContainers':
            self.__handleImagesAndRunningContainers(message=message)

    def __handleAverageReceivedPackageSize(self, message: Message):
        result = self.__handleEdgeAverage(message, 'averageReceivedPackageSize')
        for edgeName, average in result:
            self.edges[edgeName].averageReceivedPackageSize = average

    def __handleRoundTripDelay(self, message: Message):
        result = self.__handleEdgeAverage(message, 'roundTripDelay')
        for edgeName, average in result:
            self.edges[edgeName].averageRoundTripDelay = average

    def __handleEdgeAverage(self, message: Message, keyName: str) -> List[Tuple[str, float]]:
        result = []
        for item in message.content[keyName].values():
            if not isinstance(item, Average):
                continue
            if item.name is None:
                continue
            edgeName = '%s,%s' % (message.source.name, item.name)
            if edgeName not in self.edges:
                self.edges[edgeName] = Edge(
                    source=message.source.name,
                    destination=item.name,
                )
            result.append((edgeName, item.average()))

        return result

    def __handleNodeResources(self, message: Message):
        nodeName = message.source.name
        nodeResources = message.content['resources']
        self.nodeResources[nodeName] = nodeResources

    def __handleAverageProcessTime(self, message: Message):
        workerName = message.source.name
        averageProcessTime = message.content['averageProcessTime']
        self.averageProcessTime[workerName] = averageProcessTime

    def __handleResponseTime(self, message: Message):
        userName = message.source.name
        respondTime = message.content['respondTime']
        self.averageRespondTime[userName] = respondTime

    def __handleImagesAndRunningContainers(self, message: Message):
        workerName = message.source.name
        workerInfo = message.content['imagesAndRunningContainers']
        self.imagesAndRunningContainers[workerName] = workerInfo

    def __saveToPersistentStorage(self):
        self.persistentStorage.write('edges', self.edges)
        self.persistentStorage.write('nodeResources', self.nodeResources)
        self.persistentStorage.write('averageProcessTime', self.averageProcessTime)
        self.persistentStorage.write('averageRespondTime', self.averageRespondTime)
        self.persistentStorage.write('imagesAndRunningContainers', self.imagesAndRunningContainers)

    def __readFromPersistentStorage(self):
        self.edges = self.persistentStorage.read('edges')
        self.nodeResources = self.persistentStorage.read('nodeResources', )
        self.averageProcessTime = self.persistentStorage.read('averageProcessTime')
        self.averageRespondTime = self.persistentStorage.read('averageRespondTime')
        self.imagesAndRunningContainers = self.persistentStorage.read('imagesAndRunningContainers')


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
