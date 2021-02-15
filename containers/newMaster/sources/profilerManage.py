import threading
from typing import Dict
from node import ImagesAndContainers
from persistentStorage import PersistentStorage
from connection import Median


class Profiler:
    def __init__(self):
        self.lock = threading.Lock()
        self.medianPackageSize: Dict[str, Dict[str, float]] = {}
        self.medianDelay: Dict[str, Dict[str, float]] = {}
        self.nodeResources: Dict = {}
        self.medianProcessTime: Dict[str, float] = {}
        self.medianRespondTime: Dict[str, float] = {}
        self.imagesAndRunningContainers: Dict[str, ImagesAndContainers] = {}

        self._medianDelay: Dict[str, Dict[str, Median]] = {}
        self._medianProcessTime: Dict[str, Median] = {}

        self.persistentStorage: PersistentStorage = PersistentStorage()
        self.__readFromPersistentStorage()

    def _saveToPersistentStorage(self):
        self.lock.acquire()
        self.persistentStorage.write('medianPackageSize', self.medianPackageSize)
        self.persistentStorage.write('medianDelay', self.medianDelay)
        self.persistentStorage.write('nodeResources', self.nodeResources)
        self.persistentStorage.write('medianProcessTime', self.medianProcessTime)
        self.persistentStorage.write('medianRespondTime', self.medianRespondTime)
        self.persistentStorage.write('imagesAndRunningContainers', self.imagesAndRunningContainers)
        self.lock.release()

    def __readFromPersistentStorage(self):
        self.lock.acquire()
        self.medianPackageSize = self.persistentStorage.read('medianPackageSize')
        self.medianDelay = self.persistentStorage.read('medianDelay')
        self.nodeResources = self.persistentStorage.read('nodeResources', )
        self.medianProcessTime = self.persistentStorage.read('medianProcessTime')
        self.medianRespondTime = self.persistentStorage.read('medianRespondTime')
        self.imagesAndRunningContainers = self.persistentStorage.read('imagesAndRunningContainers')
        self.lock.release()
