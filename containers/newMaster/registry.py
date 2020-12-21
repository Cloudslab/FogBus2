from datatype import Worker, NodeSpecs

class Registry:

    def __init__(self):
        self.id = 0
        self.workers = {}

    def addWoker(self, sid:str, nodeSpecs:NodeSpecs):
        self.id += 1
        self.workers[self.id] = Worker(self.id, sid, nodeSpecs)
        return self.id

    def remove(self, workerID):
        del self.workers[workerID]


if __name__ == "__main__":
    print("[*] Test Registry")
    registry = Registry()
