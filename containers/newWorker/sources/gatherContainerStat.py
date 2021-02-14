import docker
import queue
import threading
from time import time, sleep


class GatherContainerStat:

    def __init__(self, client, numThreads: int = 16):
        self._containerStatNumThreads = numThreads
        self._containers = queue.Queue()
        self._containerStats = queue.Queue()
        self.client = client

    def _runContainerStat(self):
        threading.Thread(
            target=self._listContainers).start()
        for i in range(self._containerStatNumThreads):
            threading.Thread(
                target=self._containerStatHandler,
                name='Handler-%d' % i).start()

    def _listContainers(self):
        t = time()
        while True:
            timeDiff = time() - t
            if timeDiff < 0.5:
                sleep(timeDiff)
                continue
            try:
                containerList = self.client.containers.list()
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
                'remote-logger:latest',
                'user:latest',
                'worker:latest'}:
                continue
            try:
                stats = container.stats(stream=False)
                cpuUsage = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage'][
                    'total_usage']
                systemCPUUsage = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                memoryUsage = stats['memory_stats']['usage']
                peekMemoryUsage = stats['memory_stats']['max_usage']
                maxMemory = stats['memory_stats']['limit']
                resources = {
                    'systemCPUUsage': systemCPUUsage,
                    'cpuUsage': cpuUsage,
                    'memoryUsage': memoryUsage,
                    'peekMemoryUsage': peekMemoryUsage,
                    'maxMemory': maxMemory}
                self._containerStats.put((
                    container.name,
                    resources))
            except Exception:
                continue

    @staticmethod
    def snake_to_camel(snake_str):
        if snake_str == 'oct':
            return 'OCR'
        # https://stackoverflow.com/questions/19053707
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)


if __name__ == '__main__':
    pass
