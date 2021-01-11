# https://www.thepythoncode.com/article/get-hardware-system-information-python
import psutil
import platform
import GPUtil
import threading
import numpy as np
from datetime import datetime
from pprint import pformat
from typing import Any


class SystemInfoResult:

    def __init__(self,
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
                 currentCPUFrequency=None,
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
                 gpus=None):
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
        self.gpus = gpus

    def __str__(self):
        return pformat(vars(self))

    def keys(self):
        return list(dict(vars(self)).keys())

    def values(self):
        return list(dict(vars(self)).values())


class SystemInfo:

    def __init__(self, formatSize: bool):
        self.__formatSize = formatSize
        self.res: SystemInfoResult = SystemInfoResult()

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
        if event is not None:
            event.set()

        resBootTime = timeZone, bootTimestamp, dateFormatted
        self.res.bootTimeZone = timeZone
        self.res.bootTimestamp = bootTimestamp
        self.res.bootTimeDate = dateFormatted

        return resBootTime

    def operatingSystem(self, event: threading.Event = None):
        uname = platform.uname()
        if event is not None:
            event.set()
        resOS = uname.system, uname.node, uname.release, uname.version, uname.machine
        self.res.operatingSystemName = uname.system
        self.res.nodeName = uname.node
        self.res.operatingSystemReleaseName = uname.release
        self.res.operatingSystemVersion = uname.version
        self.res.operatingSystemArch = uname.machine
        return resOS

    def cpu(self, event: threading.Event = None):
        coresCount = psutil.cpu_count(logical=False)
        cpuFreq = psutil.cpu_freq()
        maxFreq = cpuFreq.max
        minFreq = cpuFreq.min
        currFreq = cpuFreq.current
        coresPercentage = []
        # CPU usage
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            coresPercentage.append(percentage)
        coresPercentage = np.asarray(coresPercentage)
        totalPercentage = psutil.cpu_percent()
        if event is not None:
            event.set()

        resCPU = coresCount, maxFreq, minFreq, currFreq, coresPercentage, totalPercentage

        self.res.totalCPUCores = coresCount
        self.res.maxCPUFrequency = maxFreq
        self.res.minCPUFrequency = minFreq
        self.res.currentCPUFrequency = currFreq
        self.res.currentTotalCPUUsagePerCore = coresPercentage
        self.res.currentTotalCPUUsage = totalPercentage
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
        if event is not None:
            event.set()

        resMemory = totalMem, availableMem, usedMem, usedPercentage, swapTotalMem, swapFreeMem, swapUsedMem, swapUsedPercentage
        self.res.totalMemory = totalMem
        self.res.availableMemory = availableMem
        self.res.usedMemory = usedMem
        self.res.usedMemoryPercentage = usedPercentage
        self.res.totalSwapMemory = swapTotalMem
        self.res.availableSwapMemory = swapFreeMem
        self.res.usedSwapMemory = swapUsedMem
        self.res.usedSwapMemoryPercentage = swapUsedPercentage
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
                # this can be catched due to the disk that
                # isn't ready
                continue
            res.append(self.__getSize(partitionUsage.total))
            res.append(self.__getSize(partitionUsage.used))
            res.append(self.__getSize(partitionUsage.free))
            res.append(self.__getSize(partitionUsage.percent))

            resPartitions.append(res)
        # get IO statistics since boot
        diskIO = psutil.disk_io_counters()
        resPartitions.append(self.__getSize(diskIO.read_bytes))
        resPartitions.append(self.__getSize(diskIO.write_bytes))
        if event is not None:
            event.set()

        resDiskIO = self.__getSize(diskIO.read_bytes), self.__getSize(diskIO.write_bytes)
        self.res.diskTotalRead = self.__getSize(diskIO.read_bytes)
        self.res.diskTotalWrite = self.__getSize(diskIO.write_bytes)
        return resDiskIO

    def network(self, event: threading.Event = None):
        resNetwork = {}
        ifAddr = psutil.net_if_addrs()
        for interfaceName, interfaceAddresses in ifAddr.items():
            for address in interfaceAddresses:
                if interfaceName not in resNetwork:
                    resNetwork[interfaceName] = [None for i in range(6)]
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
        if event is not None:
            event.set()
        resNerWorkIO = self.__getSize(networkIO.bytes_sent), self.__getSize(networkIO.bytes_recv)
        self.res.networkTotalSent = self.__getSize(networkIO.bytes_sent)
        self.res.networkTotalReceived = self.__getSize(networkIO.bytes_recv)
        return resNerWorkIO

    def gpu(self, event: threading.Event = None):
        gpus = GPUtil.getGPUs()
        resGPU = []
        for gpu in gpus:
            # get the GPU id
            gpuID = gpu.id
            # name of GPU
            gpuName = gpu.name
            # get % percentage of GPU usage of that GPU
            gpuLoad = f"{gpu.load * 100}%"
            # get free memory in MB format
            gpuFreeMemory = f"{gpu.memoryFree}MB"
            # get used memory
            gpuUsedMemory = f"{gpu.memoryUsed}MB"
            # get total memory
            gpuTotalMemory = f"{gpu.memoryTotal}MB"
            # get GPU temperature in Celsius
            gpuTemperature = f"{gpu.temperature} °C"
            gpuUUID = gpu.uuid
            resGPU.append([
                gpuID, gpuName, gpuLoad, gpuFreeMemory, gpuUsedMemory,
                gpuTotalMemory, gpuTemperature, gpuUUID
            ])
        if event is not None:
            event.set()
        self.res.gpus = resGPU
        return resGPU

    def getAll(self):
        bootTimeEvent = threading.Event()
        operatingSystemEvent = threading.Event()
        memoryEvent = threading.Event()
        diskEvent = threading.Event()
        networkEvent = threading.Event()
        gpuEvent = threading.Event()
        cpuEvent = threading.Event()

        threading.Thread(
            target=self.cpu, args=(cpuEvent,)
        ).start()
        threading.Thread(
            target=self.bootTime, args=(bootTimeEvent,)
        ).start()
        threading.Thread(
            target=self.operatingSystem, args=(operatingSystemEvent,)
        ).start()
        threading.Thread(
            target=self.memory, args=(memoryEvent,)
        ).start()
        threading.Thread(
            target=self.disk, args=(diskEvent,)
        ).start()
        threading.Thread(
            target=self.network, args=(networkEvent,)
        ).start()
        threading.Thread(
            target=self.gpu, args=(gpuEvent,)
        ).start()

        cpuEvent.wait()
        bootTimeEvent.wait()
        operatingSystemEvent.wait()
        memoryEvent.wait()
        diskEvent.wait()
        networkEvent.wait()
        gpuEvent.wait()

        return self.res


if __name__ == '__main__':
    sysInfo = SystemInfo(formatSize=True)

    print(sysInfo.getAll())
    print(sysInfo.res.keys())
    print(sysInfo.res.values())
