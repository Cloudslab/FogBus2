import sys
import logging
from node import Node, Address
from connection import Message
from logger import get_logger


class RemoteLogger(Node):
    def __init__(
            self,
            myAddr: Address,
            masterAddr: Address,
            loggerAddr: Address,
            logLevel=logging.DEBUG):
        super().__init__(myAddr, masterAddr, loggerAddr)
        self.logLevel = logLevel

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
        elif message.type == 'imageNames':
            self.__handleImageNames(message=message)

    def __handleAverageReceivedPackageSize(self, message: Message):
        pass

    def __handleAverageProcessTime(self, message: Message):
        pass

    def __handleNodeResources(self, message: Message):
        pass

    def __handleResponseTime(self, message: Message):
        pass

    def __handleRoundTripDelay(self, message: Message):
        pass

    def __handleImageNames(self, message: Message):
        self.logger.info(message.content)


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
