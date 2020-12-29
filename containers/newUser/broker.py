import logging
import threading
from logger import get_logger
from dataManager import DataManager
from message import Message
from typing import NoReturn
from collections import defaultdict
from typing import Any


class DataFrame:

    def __init__(self, data: Any, dataID: int, result: Any = None):
        self.data: Any = data
        self.dataID: int = dataID
        self.result: Any = result


class Broker:

    def __init__(
            self,
            host: str,
            port: int,
            logLevel=logging.DEBUG):
        self.logger = get_logger('User-Broker', logLevel)
        self.host = host
        self.port = port
        self.userID = None
        self.lockData: threading.Lock = threading.Lock()
        self.dataID = -1
        self.data: dict[int, DataFrame] = defaultdict(DataFrame)
        self.dataManager: DataManager = DataManager(
            host=self.host,
            port=self.port,
            logLevel=self.logger.level)

    def run(self):
        self.dataManager.run()
        threading.Thread(target=self.receivedMessageHandler).start()
        self.register()

    def register(self) -> NoReturn:
        message = {'type': 'register', 'role': 'user'}
        self.send(message)
        self.logger.info("[*] Registering ...")
        while self.userID is None:
            pass
        self.logger.info("[*] Registered with userID-%d", self.userID)

    def send(self, data) -> NoReturn:
        self.dataManager.sendingQueue.put(Message.encrypt(data))

    def receivedMessageHandler(self):
        self.logger.info('[*] Received Message Handler stated.')
        while True:
            messageEncrypted = self.dataManager.receivingQueue.get()
            message = Message.decrypt(messageEncrypted)
            if message['type'] == 'userID':
                self.userID = message['userID']
            elif message['type'] == 'result':
                dataID = message['dataID']
                self.data[dataID].result = message['result']

    def newDataID(self, data) -> int:
        self.lockData.acquire()
        self.dataID += 1
        dataID = self.dataID
        self.lockData.release()
        self.data[dataID] = DataFrame(data=data, dataID=dataID)
        return dataID

    def submit(self, appID: int, data) -> int:
        dataID = self.newDataID(data)
        message = {'type': 'submitData', 'appID': appID, 'data': data, 'dataID': dataID}
        self.dataManager.sendingQueue.put(Message.encrypt(message))
        return dataID


if __name__ == '__main__':
    broker = Broker(
        host='127.0.0.1',
        port=5000,
        logLevel=logging.DEBUG)
    broker.run()
    dataID_ = broker.submit(42, 999)
    while broker.data[dataID_].result is None:
        pass
    print(999, broker.data[dataID_].result)
