from abc import abstractmethod
from queue import Queue
from typing import Any
from typing import List
from typing import Tuple

from mysql import connector
from mysql.connector.abstracts import MySQLCursorAbstract
from mysql.connector.connection import MySQLConnection

from ..allSystemPerformance import AllSystemPerformance
from ..types import AllImages
from ..types import AllResources
from ..types import AllRunningContainers
from ....types import CPU
from ....types import Memory
from ....types import ProcessingTime

ConnCursorQueue = Queue[Tuple[MySQLConnection, MySQLCursorAbstract]]


class BaseDatabase:

    @staticmethod
    def threadSafeWrite(connCursorQueue: ConnCursorQueue, sql: str):
        conn, cursor = connCursorQueue.get()
        cursor.execute(sql)
        conn.commit()
        connCursorQueue.put((conn, cursor))

    @staticmethod
    def threadSafeRead(connCursorQueue: ConnCursorQueue, sql: str) \
            -> List[List[Any]]:
        conn, cursor = connCursorQueue.get()
        cursor.execute(sql)
        result = cursor.fetchall()
        connCursorQueue.put((conn, cursor))
        return result

    @staticmethod
    def connectionsPool(
            host: str, port: int, user: str, password: str, dbName: str,
            threadNum: int = 3, **kwargs) -> ConnCursorQueue:
        connCursorQueue = Queue()
        for i in range(threadNum):
            conn = connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=dbName,
                **kwargs)
            cursor = conn.cursor()
            connCursorQueue.put((conn, cursor))
        return connCursorQueue

    @abstractmethod
    def writeImages(self, hostID: str, images: List):
        raise NotImplementedError

    @abstractmethod
    def readImages(self, hostID: str) -> List:
        raise NotImplementedError

    @abstractmethod
    def writeRunningContainers(self, hostID: str, runningContainers: List):
        raise NotImplementedError

    @abstractmethod
    def readRunningContainers(self, hostID: str) -> List:
        raise NotImplementedError

    @abstractmethod
    def writeCPU(self, hostID: str, cpu: CPU):
        raise NotImplementedError

    @abstractmethod
    def readCPU(self, hostID: str) -> CPU:
        raise NotImplementedError

    @abstractmethod
    def writeMemory(self, hostID: str, memory: Memory):
        raise NotImplementedError

    @abstractmethod
    def readMemory(self, hostID: str) -> Memory:
        raise NotImplementedError

    @abstractmethod
    def writeDataRate(self, source: str, destination: str, dataRate: float):
        raise NotImplementedError

    @abstractmethod
    def readDataRate(self, source: str, destination: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def writeDelay(self, source: str, destination: str, delay: float):
        raise NotImplementedError

    @abstractmethod
    def readDelay(self, source: str, destination: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def writeLatency(self, source: str, destination: str, latency: float):
        raise NotImplementedError

    @abstractmethod
    def readLatency(self, source: str, destination: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def writePacketSize(self, source: str, destination: str, packetSize: float):
        raise NotImplementedError

    @abstractmethod
    def readPacketSize(self, source: str, destination: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def writeProcessingTime(self, nameConsistent: str,
                            processingTime: ProcessingTime):
        raise NotImplementedError

    @abstractmethod
    def readProcessingTime(self, nameConsistent: str) -> ProcessingTime:
        raise NotImplementedError

    @abstractmethod
    def writeResponseTime(self, nameConsistent: str, responseTime: float):
        raise NotImplementedError

    @abstractmethod
    def readResponseTime(self, nameConsistent: str, ) -> float:
        raise NotImplementedError

    @abstractmethod
    def readAllImages(self) -> AllImages:
        raise NotImplementedError

    @abstractmethod
    def readAllRunningContainers(self) -> AllRunningContainers:
        raise NotImplementedError

    @abstractmethod
    def readAllResources(self) -> AllResources:
        raise NotImplementedError

    @abstractmethod
    def readAllSystemPerformance(self) -> AllSystemPerformance:
        raise NotImplementedError
