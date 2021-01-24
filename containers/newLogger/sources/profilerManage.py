from edge import Edge
from typing import Dict, List, Tuple
from resourcesInfo import ResourcesInfo, WorkerInfo
from persistentStorage import PersistentStorage


class Profiler:
    def __init__(self):
        self.edges: Dict[str, Edge] = {}
        self.nodeResources: Dict[str, ResourcesInfo] = {}
        self.averageProcessTime: Dict[str, float] = {}
        self.averageRespondTime: Dict[str, float] = {}
        self.imagesAndRunningContainers: Dict[str, WorkerInfo] = {}

        self.persistentStorage: PersistentStorage = PersistentStorage()
        self.__readFromPersistentStorage()

    def _saveToPersistentStorage(self):
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
