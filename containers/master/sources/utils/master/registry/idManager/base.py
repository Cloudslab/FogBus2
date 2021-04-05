from threading import Lock


class BaseIDManager:
    def __init__(self):
        self.lock = Lock()
        self.currentID: int = 0

    def next(self) -> str:
        self.lock.acquire()
        self.currentID += 1
        ret = self.currentID
        self.lock.release()
        return str(ret)
