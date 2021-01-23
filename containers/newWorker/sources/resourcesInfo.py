# https://www.thepythoncode.com/article/get-hardware-system-information-python
import psutil
import platform
import GPUtil
import threading
from datetime import datetime
from pprint import pformat
from typing import List, Set
from hashlib import sha256


class Dictionary:

    def _dict(self):
        publicItems = {}

        for key, value in self.__dict__.items():
            if '_' == key[0]:
                continue
            publicItems[key] = value
        return publicItems

    def __repr__(self):
        return self._dict().__repr__()

    def __iter__(self):
        for k, v in self._dict().items():
            yield k, v


class WorkerInfo(Dictionary):

    def __init__(
            self,
            images: Set[str] = None,
            containers: Set[str] = None,
    ):
        self.images: Set[str] = images
        self.containers: Set[str] = containers


class ResourcesInfo(Dictionary):

    def __init__(self,
                 currentTimestamp=None,
                 bootTimeZone=None,
                 bootTimestamp=None,
                 bootTimeDate=None,
                 operatingSystemReleaseName=None,
                 operatingSystemVersion=None,
                 operatingSystemName=None,
                 operatingSystemArch=None,
                 nodeName=None,
                 physicalCPUCores=None,
                 totalCPUCores=None,
                 maxCPUFrequency=None,
                 minCPUFrequency=None,
                 currentCPUFrequency=0,
                 currentTotalCPUUsage=None,
                 currentTotalCPUUsagePerCore=None,
                 totalMemory=None,
                 availableMemory=None,
                 usedMemory=None,
                 usedMemoryPercentage=None,
                 totalSwapMemory=None,
                 availableSwapMemory=None,
                 usedSwapMemory=None,
                 usedSwapMemoryPercentage=None,
                 networkTotalReceived=None,
                 networkTotalSent=None,
                 diskTotalRead=None,
                 diskTotalWrite=None,
                 disk=None,
                 gpus=None):
        self.currentTimestamp = currentTimestamp
        self.bootTimeZone = bootTimeZone
        self.bootTimestamp = bootTimestamp
        self.bootTimeDate = bootTimeDate
        self.operatingSystemName = operatingSystemName
        self.nodeName = nodeName
        self.operatingSystemReleaseName = operatingSystemReleaseName
        self.operatingSystemVersion = operatingSystemVersion
        self.operatingSystemArch = operatingSystemArch

        self.physicalCPUCores = physicalCPUCores
        self.totalCPUCores = totalCPUCores
        self.maxCPUFrequency = maxCPUFrequency
        self.minCPUFrequency = minCPUFrequency
        self.currentCPUFrequency = currentCPUFrequency
        self.currentTotalCPUUsage = currentTotalCPUUsage
        self.currentTotalCPUUsagePerCore = currentTotalCPUUsagePerCore
        self.totalMemory = totalMemory
        self.availableMemory = availableMemory
        self.usedMemory = usedMemory
        self.usedMemoryPercentage = usedMemoryPercentage
        self.totalSwapMemory = totalSwapMemory
        self.availableSwapMemory = availableSwapMemory
        self.usedSwapMemory = usedSwapMemory
        self.usedSwapMemoryPercentage = usedSwapMemoryPercentage
        self.networkTotalReceived = networkTotalReceived
        self.networkTotalSent = networkTotalSent
        self.diskTotalRead = diskTotalRead
        self.diskTotalWrite = diskTotalWrite
        self.disk = disk
        self.gpus = gpus
        Dictionary.__init__(self)

    def __str__(self):
        return pformat(vars(self))


class Resources:

    def __init__(self, formatSize: bool = False):
        self.__formatSize = formatSize
        self.__res: ResourcesInfo = ResourcesInfo()
        self.__uniqueID: str = None

        self.threads = [self.cpu,
                        self.bootTime,
                        self.operatingSystem,
                        self.memory,
                        self.disk,
                        self.network,
                        self.gpu,
                        ]

    def __getSize(self, bytes_, suffix="B"):
        if not self.__formatSize:
            return bytes_
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes_ < factor:
                return f"{bytes_:.2f}{unit}{suffix}"
            bytes_ /= factor

    def bootTime(self, event: threading.Event = None):
        bootTimeTimestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(bootTimeTimestamp)
        timeZone = datetime.now().astimezone().strftime(
            "%z")
        bootTimestamp = bt.timestamp()
        dateFormatted = f"{bt.month}/{bt.day}/{bt.year} {bt.hour}:{bt.minute}:{bt.second}"

        resBootTime = timeZone, bootTimestamp, dateFormatted
        self.__res.bootTimeZone = timeZone
        self.__res.bootTimestamp = bootTimestamp
        self.__res.bootTimeDate = dateFormatted
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resBootTime

    def operatingSystem(self, event: threading.Event = None):
        uname = platform.uname()
        resOS = uname.system, uname.node, uname.release, uname.version, uname.machine
        self.__res.operatingSystemName = uname.system
        self.__res.nodeName = uname.node
        self.__res.operatingSystemReleaseName = uname.release
        self.__res.operatingSystemVersion = uname.version
        self.__res.operatingSystemArch = uname.machine
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resOS

    def cpu(self, event: threading.Event = None):
        physicalCoresCount = psutil.cpu_count(logical=False)
        totalCoresCount = psutil.cpu_count(logical=True)
        cpuFreq = psutil.cpu_freq()
        maxFreq = cpuFreq.max
        minFreq = cpuFreq.min
        currFreq = cpuFreq.current
        coresPercentage = []
        # CPU usage
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            coresPercentage.append(percentage)
        totalPercentage = psutil.cpu_percent()

        resCPU = physicalCoresCount, totalCoresCount, maxFreq, minFreq, currFreq, coresPercentage, totalPercentage
        self.__res.physicalCPUCores = physicalCoresCount
        self.__res.totalCPUCores = totalCoresCount
        self.__res.maxCPUFrequency = maxFreq
        self.__res.minCPUFrequency = minFreq
        self.__res.currentCPUFrequency = currFreq
        self.__res.currentTotalCPUUsagePerCore = coresPercentage
        self.__res.currentTotalCPUUsage = totalPercentage
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resCPU

    def memory(self, event: threading.Event = None):
        systemVirtualMemory = psutil.virtual_memory()
        totalMem = self.__getSize(systemVirtualMemory.total)
        availableMem = self.__getSize(systemVirtualMemory.available)
        usedMem = self.__getSize(systemVirtualMemory.used)
        usedPercentage = systemVirtualMemory.percent
        swap = psutil.swap_memory()
        swapTotalMem = self.__getSize(swap.total)
        swapFreeMem = self.__getSize(swap.free)
        swapUsedMem = self.__getSize(swap.used)
        swapUsedPercentage = swap.percent

        resMemory = totalMem, availableMem, usedMem, usedPercentage, swapTotalMem, swapFreeMem, swapUsedMem, swapUsedPercentage
        self.__res.totalMemory = totalMem
        self.__res.availableMemory = availableMem
        self.__res.usedMemory = usedMem
        self.__res.usedMemoryPercentage = usedPercentage
        self.__res.totalSwapMemory = swapTotalMem
        self.__res.availableSwapMemory = swapFreeMem
        self.__res.usedSwapMemory = swapUsedMem
        self.__res.usedSwapMemoryPercentage = swapUsedPercentage
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resMemory

    def disk(self, event: threading.Event = None):
        partitions = psutil.disk_partitions()
        resPartitions = []
        for partition in partitions:
            res = [
                partition.device,
                partition.mountpoint,
                partition.fstype]
            try:
                partitionUsage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # this can be caught due to the disk that
                # isn't ready
                continue
            res.append(self.__getSize(partitionUsage.total))
            res.append(self.__getSize(partitionUsage.used))
            res.append(self.__getSize(partitionUsage.free))
            res.append(partitionUsage.percent)

            resPartitions.append(res)
        # get IO statistics since boot
        diskIO = psutil.disk_io_counters()
        resPartitions.append(self.__getSize(diskIO.read_bytes))
        resPartitions.append(self.__getSize(diskIO.write_bytes))
        resDiskIO = self.__getSize(diskIO.read_bytes), self.__getSize(diskIO.write_bytes)
        self.__res.diskTotalRead = self.__getSize(diskIO.read_bytes)
        self.__res.diskTotalWrite = self.__getSize(diskIO.write_bytes)
        self.__res.disk = resPartitions[0]
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resDiskIO, resPartitions

    def network(self, event: threading.Event = None):
        resNetwork = {}
        ifAddr = psutil.net_if_addrs()
        for interfaceName, interfaceAddresses in ifAddr.items():
            for address in interfaceAddresses:
                if interfaceName not in resNetwork:
                    resNetwork[interfaceName] = [None for _ in range(6)]
                if str(address.family) == 'AddressFamily.AF_INET':
                    resNetwork[interfaceName][0] = address.address
                    resNetwork[interfaceName][1] = address.netmask
                    resNetwork[interfaceName][2] = address.broadcast
                elif str(address.family) == 'AddressFamily.AF_PACKET':
                    resNetwork[interfaceName][3] = address.address
                    resNetwork[interfaceName][4] = address.netmask
                    resNetwork[interfaceName][5] = address.broadcast
        networkIO = psutil.net_io_counters()
        resNetwork['total'] = self.__getSize(networkIO.bytes_sent), self.__getSize(networkIO.bytes_recv)
        resNetworkIO = self.__getSize(networkIO.bytes_sent), self.__getSize(networkIO.bytes_recv)
        self.__res.networkTotalSent = self.__getSize(networkIO.bytes_sent)
        self.__res.networkTotalReceived = self.__getSize(networkIO.bytes_recv)
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resNetworkIO

    def gpu(self, event: threading.Event = None):
        gpus = GPUtil.getGPUs()
        resGPU = []
        for gpu in gpus:
            resGPU.append([
                gpu.id, gpu.name, gpu.load * 100, gpu.memoryFree, gpu.memoryUsed,
                gpu.memoryTotal, gpu.temperature, gpu.uuid
            ])
        self.__res.gpus = resGPU
        event.set()
        self.__res.currentTimestamp = datetime.now().timestamp()
        return resGPU

    def all(self):

        events: List[threading.Event] = []
        for thread in self.threads:
            event = threading.Event()
            events.append(event)
            threading.Thread(
                target=thread,
                args=(event,)
            ).start()

        for event in events:
            event.wait()
        self.uniqueID(getInfo=False)
        result = self.__res
        for event in events:
            event.clear()
        return result

    def uniqueID(self, getInfo=True):
        if self.__uniqueID is not None:
            return self.__uniqueID
        if getInfo:
            self.all()
        items = [
            self.__res.operatingSystemReleaseName,
            self.__res.operatingSystemVersion,
            self.__res.operatingSystemName,
            self.__res.operatingSystemArch,
            self.__res.physicalCPUCores,
            self.__res.totalCPUCores,
            self.__res.maxCPUFrequency,
            self.__res.minCPUFrequency,
            self.__res.totalMemory,
            self.__res.totalSwapMemory,
            self.__res.disk[:4]
        ]
        info = ''.join(str(items))
        self.__uniqueID = sha256(info.encode('utf-8')).hexdigest()
        return self.__uniqueID


if __name__ == '__main__':
    resources = Resources(formatSize=True)
    resourcesAll = resources.all()
    uniqueID = resources.uniqueID()
    print(uniqueID)
