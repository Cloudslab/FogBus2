# https://www.thepythoncode.com/article/get-hardware-system-information-python
import psutil
import platform
import GPUtil
import threading
import numpy as np
import os
import csv
from datetime import datetime
from pprint import pformat
from time import sleep


class SystemInfoResult:

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
        self.gpus = gpus

    def __str__(self):
        self.currentTimestamp = datetime.now().timestamp()
        return pformat(vars(self))

    def keys(self, changing=None):
        self.currentTimestamp = datetime.now().timestamp()
        if changing is None:
            return list(dict(vars(self)).keys())
        if not changing:
            return [
                'currentTimestamp',
                'bootTimeZone',
                'bootTimestamp',
                'bootTimeDate',
                'operatingSystemName',
                'nodeName',
                'operatingSystemReleaseName',
                'operatingSystemVersion',
                'operatingSystemArch',
                'physicalCPUCores',
                'totalCPUCores',
                'maxCPUFrequency',
                'minCPUFrequency',
                'totalMemory',
                'totalSwapMemory',
            ]
        if changing:
            return [
                'currentTimestamp',
                'currentCPUFrequency',
                'currentTotalCPUUsage',
                'currentTotalCPUUsagePerCore',
                'availableMemory',
                'availableSwapMemory',
                'networkTotalReceived',
                'networkTotalSent',
                'diskTotalRead',
                'diskTotalWrite',
                'gpus',
            ]

    def values(self, changing=None):
        self.currentTimestamp = datetime.now().timestamp()
        allProperties = vars(self)
        if changing is None:
            return list(dict(allProperties).values())
        if not changing:
            return [
                allProperties['currentTimestamp'],
                allProperties['bootTimeZone'],
                allProperties['bootTimestamp'],
                allProperties['bootTimeDate'],
                allProperties['operatingSystemName'],
                allProperties['nodeName'],
                allProperties['operatingSystemReleaseName'],
                allProperties['operatingSystemVersion'],
                allProperties['operatingSystemArch'],
                allProperties['physicalCPUCores'],
                allProperties['totalCPUCores'],
                allProperties['maxCPUFrequency'],
                allProperties['minCPUFrequency'],
                allProperties['totalMemory'],
                allProperties['totalSwapMemory'],
            ]
        if changing:
            return [
                allProperties['currentTimestamp'],
                allProperties['currentCPUFrequency'],
                allProperties['currentTotalCPUUsage'],
                allProperties['currentTotalCPUUsagePerCore'],
                allProperties['availableMemory'],
                allProperties['availableSwapMemory'],
                allProperties['networkTotalReceived'],
                allProperties['networkTotalSent'],
                allProperties['diskTotalRead'],
                allProperties['diskTotalWrite'],
                allProperties['gpus'],
            ]


class SystemInfo:

    def __init__(self, formatSize: bool):
        self.__formatSize = formatSize
        self.res: SystemInfoResult = SystemInfoResult()

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
        coresPercentage = np.asarray(coresPercentage)
        totalPercentage = psutil.cpu_percent()
        if event is not None:
            event.set()

        resCPU = physicalCoresCount, totalCoresCount, maxFreq, minFreq, currFreq, coresPercentage, totalPercentage

        self.res.physicalCPUCores = physicalCoresCount
        self.res.totalCPUCores = totalCoresCount
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

        events = []
        for thread in self.threads:
            event = threading.Event()
            events.append(event)
            threading.Thread(
                target=thread,
                args=(event,)
            ).start()

        for event in events:
            event.wait()

        return self.res

    def recordPerSeconds(self, seconds: float, logFilename: str):
        threading.Thread(
            target=self.__recordPerSeconds,
            args=(seconds, logFilename)
        ).start()

    def __recordPerSeconds(self, seconds: float, logFilename: str):
        self.getAll()
        unchangingLog = 'unchanging_' + logFilename
        changingLog = 'changing_' + logFilename

        if not os.path.exists(unchangingLog):
            f = open(unchangingLog, 'w')
            title = self.res.keys(changing=False)
            for name in title[:-1]:
                f.write(name + ', ')
            f.write(title[-1] + '\r\n')
            while self.res.physicalCPUCores is None:
                sleep(1)
            values = self.res.values(changing=False)
            for value in values[:-1]:
                f.write(str(value) + ', ')
            f.write(str(values[-1]) + '\r\n')
            f.close()

        if not os.path.exists(changingLog):
            f = open(changingLog, 'w')
            title = self.res.keys(changing=True)
            for name in title[:-1]:
                f.write(name + ', ')

            f.write(title[-1] + '\r\n')
            f.close()

        while True:
            if self.res.physicalCPUCores is None:
                sleep(1)
                continue
            values = self.res.values(changing=True)
            with open(changingLog, 'a') as logFile:
                writer = csv.writer(logFile, quoting=csv.QUOTE_ALL)
                writer.writerow(values)
                logFile.close()
            self.getAll()
            sleep(seconds)


if __name__ == '__main__':
    sysInfo = SystemInfo(formatSize=True)
    sysInfo.recordPerSeconds(5, 'testLog.csv')

    print(sysInfo.getAll())
    print(sysInfo.res.keys())
    print(sysInfo.res.values())
