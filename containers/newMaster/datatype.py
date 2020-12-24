class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "Cores: %d\tRam: %d GB\tDisk: %d GB\tNetwork: %d Mbps" % (self.cores, self.ram, self.disk, self.network)


class Master:

    def __init__(self, host: str, port: int, masterID: int = 0):
        self.host = host
        self.port = port
        self.masterID = masterID


class Worker:

    def __init__(self, workerID: int, registrySocketID: str, specs: NodeSpecs):
        self.workerID = workerID
        self.registrySocketID = registrySocketID
        self.specs = specs
        self.taskSocketID = None


class User:

    def __init__(self, userID: int, registrySocketID: str):
        self.userID = userID
        self.registrySocketID = registrySocketID
        self.taskSocketID = None


class Task:

    def __init__(self, userID: int, taskID: int, appID: int, dataID: int):
        self.userID = userID
        self.taskID = taskID
        self.appID = appID
        self.dataID = dataID
        self.resultID = None
        self.workerID = None
        self.outputData = None
        self.hasDone = False
