import sys
import logging
from node import Node, Address
from connection import Message, Average
from logger import get_logger
from edge import Edge
from typing import Dict


class RemoteLogger(Node):
    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            logLevel=logging.DEBUG):
        super().__init__(myAddr, masterAddr, loggerAddr)
        self.logLevel = logLevel

        self.edges: Dict[str, Edge] = {}

    def run(self):
        self.role = 'RemoteLogger'
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
        for item in message.content['averageReceivedPackageSize'].values():
            if not isinstance(item, Average):
                continue
            if item.name is None:
                continue
            edgeName = '%s,%s' % (item.name, message.source.name)
            if edgeName not in self.edges:
                self.edges[edgeName] = Edge(
                    source=item.name,
                    destination=message.source.name,
                )
            self.edges[edgeName].averagePackageSize = item.average()

    def __handleAverageProcessTime(self, message: Message):
        pass

    def __handleNodeResources(self, message: Message):
        pass

    def __handleResponseTime(self, message: Message):
        pass

    def __handleRoundTripDelay(self, message: Message):
        pass

    def __handleImagesAndRunningContainers(self, message: Message):
        pass


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
