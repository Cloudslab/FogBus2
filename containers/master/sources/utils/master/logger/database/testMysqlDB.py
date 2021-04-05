import unittest
from random import randint
from random import random
from typing import Dict

from .mysqlDB import MySQLDatabase
from ..allSystemPerformance import AllSystemPerformance
from ....types import CPU
from ....types import Images
from ....types import Memory
from ....types import ProcessingTime
from ....types import RunningContainers


class MySQLTest(unittest.TestCase):
    hostID = 'HOST_ID_TEST'
    source = 'SOURCE_TEST'
    destination = 'DESTINATION_TEST'
    db = MySQLDatabase(user='root', password='passwordForRoot')

    @staticmethod
    def random():
        return round(random(), 5)

    def sameDict(self, a: Dict, b: Dict) -> bool:
        if len(a) != len(b):
            return False
        for key, value in a.items():
            if isinstance(b[key], Dict):
                if not isinstance(a[key], Dict):
                    return False
                if not self.sameDict(b[key], a[key]):
                    return False
                continue
            if b[key] != a[key]:
                return False
        return True

    def testImages(self):
        images = Images([1, 2, 3, 4])
        self.db.writeImages(self.hostID, images)
        self.assertEqual(images, self.db.readImages(self.hostID))

    def testRunningContainers(self):
        runningContainers = RunningContainers([1, 2, 3, 4, 5])
        self.db.writeRunningContainers(self.hostID, runningContainers)
        self.assertEqual(
            runningContainers,
            self.db.readRunningContainers(self.hostID))

    def testCPU(self):
        cpu = CPU()
        self.db.writeCPU(self.hostID, cpu)
        cpuInDict = cpu.toDict()
        readCPU = self.db.readCPU(self.hostID)
        readCPUInDict = readCPU.toDict()
        self.assertTrue(self.sameDict(cpuInDict, readCPUInDict))

    def testMemory(self):
        memory = Memory()
        self.db.writeMemory(self.hostID, memory)
        memoryInDict = memory.toDict()
        readMemory = self.db.readMemory(self.hostID)
        readMemoryInDict = readMemory.toDict()
        self.assertTrue(self.sameDict(memoryInDict, readMemoryInDict))

    def testDataRate(self):
        dataRate = self.random()
        self.db.writeDataRate(self.source, self.destination, dataRate)
        self.assertEqual(
            dataRate,
            self.db.readDataRate(self.source, self.destination))

    def testDelay(self):
        delay = self.random()
        self.db.writeDelay(self.source, self.destination, delay)
        self.assertEqual(
            delay,
            self.db.readDelay(self.source, self.destination))

    def testLatency(self):
        latency = self.random()
        self.db.writeLatency(self.source, self.destination, latency)
        self.assertEqual(
            latency,
            self.db.readLatency(self.source, self.destination))

    def testPacketSize(self):
        packetSize = randint(0, 1024)
        self.db.writePacketSize(self.source, self.destination, packetSize)
        self.assertEqual(
            packetSize,
            self.db.readPacketSize(self.source, self.destination))

    def testProcessingTime(self):
        nameConsistent = 'apple_banana42'
        processingTime = ProcessingTime()
        self.db.writeProcessingTime(nameConsistent, processingTime)
        readProcessingTime = self.db.readProcessingTime(nameConsistent)
        self.assertTrue(
            self.sameDict(processingTime.toDict(), readProcessingTime.toDict()))

    def testResponseTime(self):
        nameConsistent = 'banana_apple1024'
        responseTime = self.random()
        self.db.writeResponseTime(nameConsistent, responseTime)
        self.assertEqual(responseTime, self.db.readResponseTime(nameConsistent))

    def testReadAllImages(self):
        images = self.db.readAllImages()
        self.assertTrue(isinstance(images, dict))

    def testReadAllRunningContainers(self):
        runningContainers = self.db.readAllRunningContainers()
        self.assertTrue(isinstance(runningContainers, dict))

    def testReadAllResources(self):
        resources = self.db.readAllResources()
        self.assertTrue(isinstance(resources, dict))

    def testReadAllSystemPerformance(self):
        systemPerformance = self.db.readAllSystemPerformance()
        self.assertTrue(isinstance(systemPerformance, AllSystemPerformance))


if __name__ == '__main__':
    unittest.main()
