import threading
from typing import Dict
from resourcesInfo import ResourcesInfo, ImagesAndContainers
from persistentStorage import PersistentStorage


class Profiler:
    def __init__(self):
        self.lock = threading.Lock()
        self.averagePackageSize: Dict[str, Dict[str, float]] = {}
        self.averageDelay: Dict[str, Dict[str, float]] = {}
        self.nodeResources: Dict[str, ResourcesInfo] = {}
        self.averageProcessTime: Dict[str, float] = {}
        self.averageRespondTime: Dict[str, float] = {}
        self.imagesAndRunningContainers: Dict[str, ImagesAndContainers] = {}

        self.persistentStorage: PersistentStorage = PersistentStorage()
        self.__readFromPersistentStorage()

    def _saveToPersistentStorage(self):
        self.lock.acquire()
        self.persistentStorage.write('averagePackageSize', self.averagePackageSize)
        self.persistentStorage.write('averageDelay', self.averageDelay)
        self.persistentStorage.write('nodeResources', self.nodeResources)
        self.persistentStorage.write('averageProcessTime', self.averageProcessTime)
        self.persistentStorage.write('averageRespondTime', self.averageRespondTime)
        self.persistentStorage.write('imagesAndRunningContainers', self.imagesAndRunningContainers)
        self.lock.release()

    def __readFromPersistentStorage(self):
        self.lock.acquire()
        self.averagePackageSize = self.persistentStorage.read('averagePackageSize')
        self.averageDelay = self.persistentStorage.read('averageDelay')
        self.nodeResources = self.persistentStorage.read('nodeResources', )
        self.averageProcessTime = self.persistentStorage.read('averageProcessTime')
        self.averageRespondTime = self.persistentStorage.read('averageRespondTime')
        self.imagesAndRunningContainers = self.persistentStorage.read('imagesAndRunningContainers')
        self.lock.release()
