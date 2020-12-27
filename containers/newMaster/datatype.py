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

    def __init__(self, workerID: int, socketID: int, specs: NodeSpecs):
        self.workerID = workerID
        self.socketID = socketID
        self.specs = specs


class User:

    def __init__(self, userID: int, socketID: int):
        self.userID = userID
        self.socketID = socketID


class Task:

    def __init__(self, workerID: int, userID: int, taskID: int, appID: int, dataID: int):
        self.workerID = workerID
        self.userID = userID
        self.taskID = taskID
        self.appID = appID
        self.dataID = dataID
        self.resultID = None
        self.hasDone = False
