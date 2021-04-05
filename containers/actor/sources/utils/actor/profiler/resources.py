from psutil import cpu_count as cpuCount
from psutil import cpu_freq as cpuFrequency
from psutil import cpu_percent as cpuPercent
from psutil import virtual_memory as virtualMemory

from ...component.basic import BasicComponent
from ...types.hostProfiles import ActorResources


class ResourcesProfiler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            resources: ActorResources = ActorResources()):
        self.resources = resources
        self.basicComponent = basicComponent

    def profileResources(self):
        # self.basicComponent.debugLogger.info('Profiling Resources...')
        self.resources.cpu.cores = self.getCPUCores()
        self.resources.cpu.frequency = self.getCPUFrequency()
        self.resources.cpu.utilization = self.getCPUUtilization()
        self.resources.cpu.utilizationPeak = self.getCPUUtilizationPeak()
        self.resources.memory.maximum = self.getMemoryMaximum()
        self.resources.memory.utilization = self.getMemoryUtilization()
        self.resources.memory.utilizationPeak = self.getMemoryUtilizationPeak()

    @staticmethod
    def getCPUFrequency():
        cpuFreq = cpuFrequency()
        if cpuFreq is None:
            return 2400.
        currFrequency = cpuFreq.current
        return float(currFrequency)

    @staticmethod
    def getCPUCores():
        totalCores = cpuCount(logical=True)
        return totalCores

    @staticmethod
    def getCPUUtilization():
        utilization = cpuPercent(interval=.5) / 100
        return round(utilization, 3)

    @staticmethod
    def getCPUUtilizationPeak():
        # TODO: Implement
        return 1.

    @staticmethod
    def getMemoryUtilization():
        vMem = virtualMemory()
        used = vMem.used
        total = vMem.total
        utilization = used / total
        return round(utilization, 3)

    @staticmethod
    def getMemoryUtilizationPeak():
        # TODO: Implement
        return 1.

    @staticmethod
    def getMemoryMaximum():
        maximum = virtualMemory().total
        return maximum
