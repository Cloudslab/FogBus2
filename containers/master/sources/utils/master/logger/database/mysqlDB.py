from abc import ABC
from json import dumps
from json import loads
from typing import Dict
from typing import Set
from typing import Union

from .base import BaseDatabase
from ..allSystemPerformance import AllDataRate
from ..allSystemPerformance import AllDelay
from ..allSystemPerformance import AllLatency
from ..allSystemPerformance import AllPacketSize
from ..allSystemPerformance import AllProcessingTime
from ..allSystemPerformance import AllResponseTime
from ..allSystemPerformance import AllSystemPerformance
from ..types import AllImages
from ..types import AllResources
from ..types import AllRunningContainers
from ....component.platformInfo import PlatformInfo
from ....types import ActorResources
from ....types import CPU
from ....types import Images
from ....types import Memory
from ....types import ProcessingTime
from ....types import RunningContainers


class MySQLDatabase(BaseDatabase, ABC):

    def __init__(
            self,
            user: str,
            password: str,
            host: str = '127.0.0.1',
            port: int = 3306,
            dbImages: str = 'FogBus2_Images',
            dbResources: str = 'FogBus2_Resources',
            dbSystemPerformance: str = 'FogBus2_SystemPerformance',
            **kwargs):
        BaseDatabase.__init__(self)
        self.connImages = self.connectionsPool(
            host=host,
            port=port,
            user=user,
            password=password,
            dbName=dbImages,
            **kwargs)
        self.connResources = self.connectionsPool(
            host=host,
            port=port,
            user=user,
            password=password,
            dbName=dbResources,
            **kwargs)
        self.connSystemPerformance = self.connectionsPool(
            host=host,
            port=port,
            user=user,
            password=password,
            dbName=dbSystemPerformance,
            **kwargs)

    def writeSystemPerformanceSourceDestination(
            self,
            tableName: str,
            source: str,
            destination: str,
            data: Union[float, int]):
        data = str(data)
        sql = 'INSERT INTO %s' \
              ' (source,destination,%s) ' \
              'VALUES("%s","%s",%s) ' \
              'ON DUPLICATE KEY ' \
              'UPDATE %s=%s;' \
              % (
                  tableName,
                  tableName,
                  source, destination, data,
                  tableName, data)
        self.threadSafeWrite(self.connSystemPerformance, sql)

    def readSystemPerformanceSourceDestination(
            self,
            tableName: str,
            source: str,
            destination: str):
        sql = 'SELECT %s ' \
              'FROM %s ' \
              'WHERE source="%s" AND destination="%s"' \
              % (
                  tableName,
                  tableName,
                  source,
                  destination)
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        return result[0][0]

    def writeDataRate(self, source: str, destination: str, dataRate: float):
        self.writeSystemPerformanceSourceDestination(
            'dataRate', source, destination, dataRate)

    def readDataRate(self, source: str, destination: str) -> float:
        return self.readSystemPerformanceSourceDestination(
            'dataRate', source, destination)

    def writeDelay(self, source: str, destination: str, delay: float):
        self.writeSystemPerformanceSourceDestination(
            'delay', source, destination, delay)

    def readDelay(self, source: str, destination: str) -> float:
        return self.readSystemPerformanceSourceDestination(
            'delay', source, destination)

    def writeLatency(self, source: str, destination: str, latency: float):
        self.writeSystemPerformanceSourceDestination(
            'latency', source, destination, latency)

    def readLatency(self, source: str, destination: str) -> float:
        return self.readSystemPerformanceSourceDestination(
            'latency', source, destination)

    def writePacketSize(self, source: str, destination: str, packetSize: int):
        self.writeSystemPerformanceSourceDestination(
            'packetSize',
            source=destination,
            destination=source,
            data=packetSize)

    def readPacketSize(self, source: str, destination: str) -> float:
        return self.readSystemPerformanceSourceDestination(
            'packetSize', source, destination)

    def readSystemPerformanceNameConsistent(
            self,
            tableName: str,
            nameConsistent: str):
        sql = 'SELECT %s ' \
              'FROM %s ' \
              'WHERE nameConsistent="%s"' \
              % (
                  tableName,
                  tableName,
                  nameConsistent)
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        return result[0][0]

    def writeSystemPerformanceNameConsistent(
            self,
            tableName: str,
            nameConsistent: str,
            data: Union[float, str]):
        if isinstance(data, str):
            data = '\'%s\'' % data
        else:
            data = str(data)
        sql = 'INSERT INTO %s' \
              ' (nameConsistent,%s) ' \
              'VALUES("%s",%s) ' \
              'ON DUPLICATE KEY ' \
              'UPDATE %s=%s;' \
              % (
                  tableName,
                  tableName,
                  nameConsistent, data,
                  tableName, data)
        self.threadSafeWrite(self.connSystemPerformance, sql)

    def writeProcessingTime(self, nameConsistent: str,
                            processingTime: ProcessingTime):
        processingTimeInDict = processingTime.toDict()
        processingTimeInJson = dumps(processingTimeInDict)
        self.writeSystemPerformanceNameConsistent(
            'processingTime', nameConsistent, processingTimeInJson)

    def readProcessingTime(self, nameConsistent: str) -> ProcessingTime:
        processingTimeInJson = self.readSystemPerformanceNameConsistent(
            'processingTime', nameConsistent)
        processingTimeInDict = loads(processingTimeInJson)
        return ProcessingTime.fromDict(processingTimeInDict)

    def writeResponseTime(self, nameConsistent: str, responseTime: float):
        self.writeSystemPerformanceNameConsistent(
            'responseTime', nameConsistent, responseTime)

    def readResponseTime(self, nameConsistent: str) -> float:
        return self.readSystemPerformanceNameConsistent(
            'responseTime', nameConsistent)

    def writeResources(
            self,
            hostID,
            columnName,
            data: Union[float, int]):
        data = str(data)
        sql = 'INSERT INTO hosts (hostID,"%s") ' \
              'VALUES("%s",%s) ' \
              'ON DUPLICATE KEY ' \
              'UPDATE %s=%s' \
              % (
                  columnName,
                  hostID, data,
                  columnName, data)
        self.threadSafeWrite(self.connResources, sql)

    def readResources(self, hostID: str, columnName: str):
        sql = 'SELECT %s ' \
              'FROM hosts ' \
              'WHERE hostID="%s"' \
              % (columnName, hostID)
        result = self.threadSafeRead(self.connResources, sql)
        return result[0][0]

    def writeCPU(self, hostID: str, cpu: CPU):
        cores = cpu.cores
        frequency = cpu.frequency
        utilization = cpu.utilization
        utilizationPeak = cpu.utilizationPeak
        sql = 'INSERT INTO hosts ' \
              '(hostID,cpuCores,cpuFrequency,' \
              'cpuUtilization,cpuUtilizationPeak) ' \
              'VALUES("%s",%d,%f,%f,%f) ' \
              'ON DUPLICATE KEY UPDATE ' \
              'cpuCores=%d,' \
              'cpuFrequency=%f,' \
              'cpuUtilization=%f,' \
              'cpuUtilizationPeak=%f' \
              % (
                  hostID, cores, frequency, utilization, utilizationPeak,
                  cores,
                  frequency,
                  utilization,
                  utilizationPeak)
        self.threadSafeWrite(self.connResources, sql)

    def readCPU(self, hostID: str) -> CPU:
        sql = 'SELECT ' \
              'cpuCores,' \
              'cpuFrequency,' \
              'cpuUtilization,' \
              'cpuUtilizationPeak ' \
              'FROM hosts ' \
              'WHERE hostID="%s"' \
              % hostID
        result = self.threadSafeRead(self.connResources, sql)[0]
        cpuInDict = {
            'cores': result[0],
            'frequency': result[1],
            'utilization': result[2],
            'utilizationPeak': result[3], }
        cpu = CPU.fromDict(cpuInDict)
        return cpu

    def writeMemory(self, hostID: str, memory: Memory):
        maximum = memory.maximum
        utilization = memory.utilization
        utilizationPeak = memory.utilizationPeak
        sql = 'INSERT INTO hosts ' \
              '(hostID,memoryMaximum,' \
              'memoryUtilization,memoryUtilizationPeak) ' \
              'VALUES("%s",%s,%s,%s) ' \
              'ON DUPLICATE KEY UPDATE ' \
              'memoryMaximum=%s,' \
              'memoryUtilization=%s,' \
              'memoryUtilizationPeak=%s' \
              % (
                  hostID, maximum, utilization, utilizationPeak,
                  maximum,
                  utilization,
                  utilizationPeak)
        self.threadSafeWrite(self.connResources, sql)

    def readMemory(self, hostID: str) -> Memory:
        sql = 'SELECT ' \
              'memoryMaximum,' \
              'memoryUtilization,' \
              'memoryUtilizationPeak ' \
              'FROM hosts ' \
              'WHERE hostID="%s"' \
              % hostID
        result = self.threadSafeRead(self.connResources, sql)
        memoryInDict = {
            'maximum': result[0],
            'utilization': result[1],
            'utilizationPeak': result[2]}
        memory = Memory.fromDict(memoryInDict)
        return memory

    def writePlatform(self, hostID: str, platformInfo: PlatformInfo):
        inDict = platformInfo.toDict()
        platformStr = dumps(inDict)
        sql = 'INSERT INTO hosts ' \
              '(hostID,' \
              'platform ) ' \
              'VALUES(\'%s\',\'%s\') ' \
              'ON DUPLICATE KEY UPDATE ' \
              'platform=\'%s\'' \
              % (
                  hostID, platformStr, platformStr)
        self.threadSafeWrite(self.connResources, sql)

    def readPlatform(self, hostID: str) -> PlatformInfo:
        sql = 'SELECT ' \
              'platform ' \
              'FROM hosts ' \
              'WHERE hostID=%s' \
              % hostID
        result = self.threadSafeRead(self.connResources, sql)
        platformStr = result[0][0]
        platformJson = loads(platformStr)
        platformInfo = PlatformInfo.fromDict(platformJson)
        return platformInfo

    def writeHostIDImages(self, columnName, hostID, data: Set):
        data = dumps(list(data))
        sql = 'INSERT INTO hosts (hostID,%s) ' \
              'VALUES(\'%s\',\'%s\') ' \
              'ON DUPLICATE KEY ' \
              'UPDATE %s=\'%s\'' \
              % (
                  columnName,
                  hostID, data,
                  columnName, data)
        self.threadSafeWrite(self.connImages, sql)

    def readHostIDImages(self, columnName: str, hostID: str):
        sql = 'SELECT %s ' \
              'FROM hosts ' \
              'WHERE hostID="%s"' \
              % (columnName, hostID)
        result = self.threadSafeRead(self.connImages, sql)
        return result[0][0]

    def writeImages(self, hostID: str, images: Images):
        self.writeHostIDImages('images', hostID, images)

    def readImages(self, hostID: str) -> Images:
        images = self.readHostIDImages('images', hostID)
        return set(loads(images))

    def writeRunningContainers(
            self,
            hostID: str,
            runningContainers: RunningContainers):

        if not isinstance(runningContainers, set):
            return
        if not len(runningContainers) > 0:
            return
        self.writeHostIDImages(
            'runningContainers', hostID, runningContainers)

    def readRunningContainers(self, hostID: str) -> RunningContainers:
        runningContainers = self.readHostIDImages('runningContainers', hostID)
        return set(loads(runningContainers))

    def readAllImages(self) -> AllImages:
        sql = 'SELECT hostID,images ' \
              'FROM hosts'
        result = self.threadSafeRead(self.connImages, sql)
        images: Dict[str, Images] = {}
        for hostID, imagesInJson in result:
            images[hostID] = set(loads(imagesInJson))
        return images

    def readAllRunningContainers(self) -> AllRunningContainers:
        sql = 'SELECT hostID,runningContainers ' \
              'FROM hosts'
        result = self.threadSafeRead(self.connImages, sql)
        runningContainers: Dict[str, RunningContainers] = {}
        for hostID, runningContainersInJson in result:
            try:
                runningContainers[hostID] = set(loads(runningContainersInJson))
            except TypeError:
                continue
        return runningContainers

    def readAllResources(self) -> AllResources:
        sql = 'SELECT ' \
              'hostID,' \
              'cpuCores,cpuFrequency,cpuUtilization,cpuUtilizationPeak,' \
              'memoryMaximum,memoryUtilization,memoryUtilizationPeak,platform ' \
              'FROM hosts'
        result = self.threadSafeRead(self.connResources, sql)
        actorResources: Dict[str, ActorResources] = {}
        for hostID, \
            cpuCores, cpuFrequency, cpuUtilization, cpuUtilizationPeak, \
            memoryMaximum, memoryUtilization, memoryUtilizationPeak, \
            platformInfo \
                in result:
            cpuInDict = {
                'cores': cpuCores,
                'frequency': cpuFrequency,
                'utilization': cpuUtilization,
                'utilizationPeak': cpuUtilizationPeak}
            cpu = CPU.fromDict(cpuInDict)
            memoryInDict = {
                'maximum': memoryMaximum,
                'utilization': memoryUtilization,
                'utilizationPeak': memoryUtilizationPeak}
            memory = Memory.fromDict(memoryInDict)
            platformInfo = PlatformInfo.fromDict(loads(platformInfo))
            hostResources = ActorResources(
                cpu=cpu, memory=memory, platform=platformInfo)
            actorResources[hostID] = hostResources
        return actorResources

    def readAllSystemPerformance(self) -> AllSystemPerformance:
        systemPerformance = AllSystemPerformance(
            dataRate=self.readAllDataRate(),
            delay=self.readAllDelay(),
            latency=self.readAllLatency(),
            packetSize=self.readAllPacketSize(),
            processingTime=self.readAllProcessingTime(),
            responseTime=self.readAllResponseTime())
        return systemPerformance

    @staticmethod
    def resultToAllSourceDestination(result):
        allSourceDestination = {}
        for source, destination, data in result:
            if source not in allSourceDestination:
                allSourceDestination[source] = {}
            allSourceDestination[source][destination] = data
        return allSourceDestination

    def readAllDataRate(self) -> AllDataRate:
        sql = 'SELECT ' \
              'source,destination,dataRate ' \
              'FROM dataRate'
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        dataRate = self.resultToAllSourceDestination(result)
        return dataRate

    def readAllDelay(self) -> AllDelay:
        sql = 'SELECT ' \
              'source,destination,delay ' \
              'FROM delay'
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        delay = self.resultToAllSourceDestination(result)
        return delay

    def readAllLatency(self) -> AllLatency:
        sql = 'SELECT ' \
              'source,destination,latency ' \
              'FROM latency'
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        latency = self.resultToAllSourceDestination(result)
        return latency

    def readAllPacketSize(self) -> AllPacketSize:
        sql = 'SELECT ' \
              'source,destination,packetSize ' \
              'FROM packetSize'
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        packetSize = self.resultToAllSourceDestination(result)
        return packetSize

    def readAllProcessingTime(self) -> AllProcessingTime:
        sql = 'SELECT ' \
              'nameConsistent,processingTime ' \
              'FROM processingTime'
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        allProcessingTime = {}
        for nameConsistent, processingTimeInJson in result:
            allProcessingTime[nameConsistent] = ProcessingTime.fromDict(
                loads(processingTimeInJson))
        return allProcessingTime

    def readAllResponseTime(self) -> AllResponseTime:
        sql = 'SELECT ' \
              'nameConsistent,responseTime ' \
              'FROM responseTime'
        result = self.threadSafeRead(self.connSystemPerformance, sql)
        allResponseTime = {}
        for nameConsistent, responseTime in result:
            allResponseTime[nameConsistent] = responseTime
        return allResponseTime


if __name__ == '__main__':
    db = MySQLDatabase(
        user='root',
        password='passwordForRoot')
