class NodeSpecs:
    def __init__(self, cores, ram, disk, network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network


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
