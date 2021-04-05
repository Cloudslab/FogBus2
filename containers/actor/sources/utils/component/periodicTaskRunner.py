from threading import Thread
from time import sleep
from time import time
from typing import Callable

from .basic import BasicComponent
from ..types import PeriodicTasks


class PeriodicTaskRunner:
    def __init__(
            self,
            basicComponent: BasicComponent,
            periodicTasks: PeriodicTasks):
        self.basicComponent = basicComponent
        if periodicTasks is None:
            periodicTasks = []
        self.periodicTasks = self.mergeWithBasicPeriodicTasks(periodicTasks)
        self.startPeriodicTasks()

    def startPeriodicTasks(self):
        Thread(target=self._startPeriodicTasks).start()

    def _startPeriodicTasks(self):
        self.basicComponent.debugLogger.debug('Waiting to be registered')
        self.basicComponent.isRegistered.wait()
        self.basicComponent.debugLogger.debug(
            '%d periodic tasks are running...', len(self.periodicTasks))
        for runner, period in self.periodicTasks:
            if period <= 0:
                continue
            Thread(
                target=self.periodicTask,
                args=(runner, period)).start()

    def mergeWithBasicPeriodicTasks(
            self, periodicTasks: PeriodicTasks) -> PeriodicTasks:
        if periodicTasks is None:
            periodicTasks = []
        basicTasks = [
            (self.basicComponent.uploadMedianReceivedPacketSize, 20),
            (self.basicComponent.uploadDelays, 20)
        ]
        periodicTasks = [*basicTasks, *periodicTasks]
        return periodicTasks

    def periodicTask(self, runner: Callable, period: float):
        self.basicComponent.isRegistered.wait()
        runner()
        previousRanTime = time()
        while True:
            timeToSleep = previousRanTime + period - time()
            if timeToSleep > 0:
                sleep(timeToSleep)
            previousRanTime = time()
            runner()
