import threading
from queue import Empty
from queue import Queue
from time import sleep
from time import time
from typing import Dict

import docker


class TaskExecutorMonitor:
    _containers = Queue()
    _containerStats = Queue()
    resources: Dict = {}

    def __init__(
            self,
            dockerClient,
            numThreads: int = 4):
        self._containerStatNumThreads = numThreads
        self.dockerClient = dockerClient

    def _runContainerStat(self):

        threading.Thread(
            target=self._listContainers).start()
        for i in range(self._containerStatNumThreads):
            threading.Thread(
                target=self._containerStatHandler,
                name='Handler-%d' % i).start()
        threading.Thread(
            target=self._gatherResults).start()

    def _listContainers(self):
        t = time()
        while True:
            timeDiff = time() - t
            if timeDiff < 30:
                sleep(timeDiff)
                continue
            try:
                containerList = self.dockerClient.runningContainers.list()
            except docker.errors.NotFound:
                continue
            for container in containerList:
                self._containers.put(container)

    def _containerStatHandler(self):
        while True:
            container = self._containers.get()
            tags = container.image.tags
            if not len(tags):
                continue
            if container.image.tags[0] in {
                'master:latest',
                'remote_logger:latest',
                'user:latest',
                'actor:latest'}:
                continue
            try:
                stats = container.stats(stream=False)
                cpuUtilization = stats['cpu_stats']['cpu_utilization'][
                                     'total_utilization'] - \
                                 stats['precpu_stats']['cpu_utilization'][
                                     'total_utilization']
                systemCPUUtilization = stats['cpu_stats'][
                                           'system_cpu_utilization'] - \
                                       stats['precpu_stats'][
                                           'system_cpu_utilization']
                memoryUtilization = stats['memory_stats']['utilization']
                peekMemoryUtilization = stats['memory_stats']['max_utilization']
                maxMemory = stats['memory_stats']['limit']
                resources = {
                    'systemCPUUtilization': systemCPUUtilization,
                    'cpuUtilization': cpuUtilization,
                    'memoryUtilization': memoryUtilization,
                    'peekMemoryUtilization': peekMemoryUtilization,
                    'maxMemory': maxMemory}
                self._containerStats.put((
                    container.name,
                    resources))
            except Exception:
                continue

    def _gatherResults(self):
        while True:
            try:
                name, resources = self._containerStats.get()
                self.resources[name] = resources
            except Empty:
                sleep(5)
                continue
