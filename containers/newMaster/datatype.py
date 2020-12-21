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

    def __init__(self, host: str, port: int, id: int = 0):
        self.host = host
        self.port = port
        self.id = id


class Worker:

    def __init__(self, id: int, sid: str, specs: NodeSpecs):
        self.id = id
        self.sid = sid
        self.specs: NodeSpecs


class Task:

    def __init__(self, taskID: int, userID: int, inputData):
        self.taskID = taskID
        self.userID = userID
        self.inputData = inputData
        self.taskID = None
        self.workerID = None
        self.outputData = None
        self.hasDone = False
