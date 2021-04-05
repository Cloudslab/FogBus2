from typing import Any
from typing import Callable
from typing import Dict

from .allSystemPerformance import AllSystemPerformance
from .database import MySQLDatabase
from .types import AllDataRate
from .types import AllDelay
from .types import AllImages
from .types import AllLatency
from .types import AllPacketSize
from .types import AllProcessingTime
from .types import AllResources
from .types import AllResponseTime
from .types import AllRunningContainers
from ..config import MySQLEnvironment
from ...component.basic import BasicComponent
from ...types import LoopSourceDestination
from ...types import ActorResources
from ...types import SynchronizedAttribute


class LoggerManager:
    def __init__(
            self,
            basicComponent: BasicComponent,
            user: str = MySQLEnvironment.user,
            password: str = MySQLEnvironment.password,
            host: str = MySQLEnvironment.host,
            port: int = MySQLEnvironment.port,
            **kwargs):
        self.images: AllImages = {}
        self.resources: AllResources = {}
        self.systemPerformance = AllSystemPerformance()
        self.runningContainers: AllRunningContainers = {}
        self.basicComponent = basicComponent
        self.database = MySQLDatabase(
            user,
            password,
            host,
            port,
            **kwargs)

    def saveAll(self):
        self.saveImages()
        self.saveRunningContainers()
        self.saveResources()
        self.saveSystemPerformance()

    def saveImages(self):
        self._saveImages(self, attributeName='images')

    def saveRunningContainers(self):
        self._saveRunningContainers(self, attributeName='runningContainers')

    def saveResources(self):
        self._saveResources(self, attributeName='resources')

    def saveSystemPerformance(self):
        self.savePacketSize(self, attributeName='packetSize')
        self.saveDelay(self, attributeName='delay')
        self.saveDataRate(self, attributeName='dataRate')
        self.saveLatency(self, attributeName='latency')
        self.saveProcessingTime(self, attributeName='processingTime')
        self.saveResponseTime(self, attributeName='responseTime')

    @SynchronizedAttribute
    def savePacketSize(self, attributeName='packetSize'):
        self._saveSourceDestination(
            dictInDict=self.systemPerformance.packetSize,
            runner=self.database.writePacketSize)

    @SynchronizedAttribute
    def saveDelay(self, attributeName='delay'):
        self._saveSourceDestination(
            dictInDict=self.systemPerformance.delay,
            runner=self.database.writeDelay)

    @SynchronizedAttribute
    def saveDataRate(self, attributeName='dataRate'):
        self._saveSourceDestination(
            dictInDict=self.systemPerformance.dataRate,
            runner=self.database.writeDataRate)

    @SynchronizedAttribute
    def saveLatency(self, attributeName='latency'):
        self._saveSourceDestination(
            dictInDict=self.systemPerformance.latency,
            runner=self.database.writeLatency)

    @SynchronizedAttribute
    def saveProcessingTime(self, attributeName='processingTime'):
        for hostID, pTime in \
                self.systemPerformance.processingTime.items():
            self.database.writeProcessingTime(hostID, pTime)

    @SynchronizedAttribute
    def saveResponseTime(self, attributeName='responseTime'):
        for hostID, responseTime in \
                self.systemPerformance.responseTime.items():
            self.database.writeResponseTime(hostID, responseTime)

    def retrieveAll(self):
        self.retrieveImages()
        self.retrieveRunningContainers()
        self.retrieveResources()
        self.retrieveSystemPerformance()

    def retrieveImages(self):
        readAllImages = self.database.readAllImages()
        self.mergeImages(readAllImages)

    def retrieveRunningContainers(self):
        readAllRunningContainers = self.database.readAllRunningContainers()
        self.mergeRunningContainers(readAllRunningContainers)

    def retrieveResources(self):
        readAllResources = self.database.readAllResources()
        self.mergeResources(readAllResources)

    def retrieveSystemPerformance(self):
        readAllSystemPerformance = self.database.readAllSystemPerformance()
        self.mergeSystemPerformance(readAllSystemPerformance)

    def mergeSystemPerformance(
            self, systemPerformanceToMerge: AllSystemPerformance):
        self.mergeDataRate(systemPerformanceToMerge.dataRate)
        self.mergeDelay(systemPerformanceToMerge.delay)
        self.mergeLatency(systemPerformanceToMerge.latency)
        self.mergePacketSize(systemPerformanceToMerge.packetSize)
        self.mergeProcessingTime(systemPerformanceToMerge.processingTime)
        self.mergeResponseTime(systemPerformanceToMerge.responseTime)

    def mergeImages(self, imagesToMerge: AllImages):
        self._mergeImages(self, imagesToMerge, attributeName='images')

    def mergeRunningContainers(
            self, runningContainersToMerge: AllRunningContainers):
        self._mergeRunningContainers(
            self, runningContainersToMerge, attributeName='runningContainers')

    def mergeResources(self, resourcesToMerge: AllResources):
        self._mergeResources(self, resourcesToMerge, attributeName='resources')

    def mergeDataRate(self, allDataRate: AllDataRate):
        self._mergeSourceDestination(
            self,
            allDataRate,
            self.systemPerformance.dataRate,
            attributeName='dataRate')

    def mergeDelay(self, allDelay: AllDelay):
        self._mergeSourceDestination(
            self,
            allDelay,
            self.systemPerformance.delay,
            attributeName='delay')

    def mergeLatency(self, allLatency: AllLatency):
        self._mergeSourceDestination(
            self,
            allLatency,
            self.systemPerformance.latency,
            attributeName='latency')

    def mergePacketSize(self, allPacket: AllPacketSize):
        self._mergeSourceDestination(
            self,
            allPacket,
            self.systemPerformance.packetSize,
            attributeName='packetSize')

    def mergeProcessingTime(
            self,
            allProcessingTime: AllProcessingTime):
        self._mergeProcessingTime(
            self,
            allProcessingTime,
            attributeName='processingTime')

    def mergeResponseTime(self, allResponseTime: AllResponseTime):
        self._mergeResponseTime(
            self,
            allResponseTime,
            attributeName='responseTime')

    @SynchronizedAttribute
    def _mergeProcessingTime(
            self,
            allProcessingTime: AllProcessingTime,
            attributeName='processingTime'):
        self.systemPerformance.processingTime = {
            **self.systemPerformance.processingTime, **allProcessingTime}

    @SynchronizedAttribute
    def _mergeResponseTime(
            self,
            allResponseTime: AllResponseTime,
            attributeName='responseTime'):
        self.systemPerformance.responseTime = {
            **self.systemPerformance.responseTime, **allResponseTime}

    @SynchronizedAttribute
    def _saveRunningContainers(self, attributeName='runningContainers'):
        for hostID, runningContainers in self.runningContainers.items():
            self.database.writeRunningContainers(
                hostID, runningContainers)

    @SynchronizedAttribute
    def _saveImages(self, attributeName='images'):
        for hostID, images in self.images.items():
            self.database.writeImages(hostID, images)

    @SynchronizedAttribute
    def _saveResources(self, attributeName='resources'):
        for hostID, resources in self.resources.items():
            self._saveResourcesOfHost(hostID, resources)

    def _saveResourcesOfHost(self, hostID: str, actorResources: ActorResources):
        self.database.writeCPU(hostID, actorResources.cpu)
        self.database.writeMemory(hostID, actorResources.memory)
        self.database.writePlatform(hostID, actorResources.platform)

    @LoopSourceDestination
    def _saveSourceDestination(
            self,
            dictInDict: Dict[str, Dict[str, Any]] = None,
            runner: Callable = None):
        pass

    @SynchronizedAttribute
    def _mergeSourceDestination(self, objectA, objectB, **kwargs):
        for source, destinations in objectA.items():
            if source not in objectB:
                objectB[source] = {}
            objectB[source] = {**objectB[source], **destinations}

    @SynchronizedAttribute
    def _mergeImages(self, imagesToMerge: AllImages, attributeName='images'):
        self.images = {**self.images, **imagesToMerge}

    @SynchronizedAttribute
    def _mergeRunningContainers(
            self, readAllRunningContainers: AllRunningContainers,
            attributeName='runningContainers'):
        self.runningContainers = {
            **self.runningContainers,
            **readAllRunningContainers}

    @SynchronizedAttribute
    def _mergeResources(
            self, resources: AllResources, attributeName='resources'):
        self.resources = {**self.resources, **resources}

    def toDict(self) -> Dict:
        allImages = {}
        for host, images in self.images.items():
            allImages[host] = list(images)
        allRunningContainers = {}
        for host, runningContainers in self.runningContainers.items():
            allRunningContainers[host] = list(runningContainers)
        allResources = {}
        for host, hostResources in self.resources.items():
            allResources[host] = hostResources.toDict()
        inDict = {
            'allImages': allImages,
            'allResources': allResources,
            'allRunningContainers': allRunningContainers,
            'allSystemPerformance': self.systemPerformance.toDict()}
        return inDict

    def mergeFromDict(self, inDict: Dict):
        receivedImages = {}
        for host, images in inDict['allImages'].items():
            receivedImages[host] = set(images)
        self.mergeImages(imagesToMerge=receivedImages)

        receivedRunningContainers = {}
        for host, runningContainers in inDict['allRunningContainers'].items():
            receivedRunningContainers[host] = set(runningContainers)
        self.mergeRunningContainers(
            runningContainersToMerge=receivedRunningContainers)

        receivedResources = {}
        for host, resources in inDict['allResources'].items():
            receivedResources[host] = ActorResources.fromDict(resources)
        self.mergeResources(resourcesToMerge=receivedResources)

        receivedSystemPerformance = AllSystemPerformance.fromDict(
            inDict['allSystemPerformance'])
        self.mergeSystemPerformance(
            systemPerformanceToMerge=receivedSystemPerformance)


