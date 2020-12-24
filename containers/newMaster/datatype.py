class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "\
                Cores: %d\n\
                ram: %d GB\n\
                disk: %d GB\n\
                network: %d Mbps\n" % (self.cores, self.ram, self.disk, self.cores)


class Master:

    def __init__(self, host: str, port: int, masterID: int = 0):
        self.host = host
        self.port = port
        self.masterID = masterID


class Worker:

    def __init__(self, workerID: int, socketID: str, specs: NodeSpecs):
        self.workerID = workerID
        self.socketID = socketID
        self.specs = specs


class User:

    def __init__(self, userID: int, socketID: str):
        self.userID = userID
        self.socketID = socketID


class Task:

    def __init__(self, taskID: int, appID: int, dataID: int):
        self.taskID = taskID
        self.appID = appID
        self.dataID = dataID
        self.workerID = None
        self.outputData = None
        self.hasDone = False
