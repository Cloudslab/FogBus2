import logging
import threading
import struct
import socket
import csv
import os
from logger import get_logger
from message import Message
from time import time
from collections import defaultdict


class ConnectionIO:

    def __init__(self):
        self.__received: int = 0
        self.__receivedCount: int = 0
        self.__sent: int = 0
        self.__sentCount: int = 0
        self.receivedPerSecond = 0
        self.sentPerSecond = 0
        self.__t = time()
        self.__lastReceived = 0
        self.__lastSent = 0

    def received(self, bytes_: int):
        self.__received += bytes_
        self.__receivedCount += 1
        t = time()
        t_diff = t - self.__t
        if t_diff > 1:
            self.__t = t
            self.receivedPerSecond = (self.__received - self.__lastReceived) / t_diff
            self.__lastReceived = self.__received

    def sent(self, bytes_: int):
        self.__sent += bytes_
        self.__sentCount += 1
        t = time()
        t_diff = t - self.__t
        if t_diff > 1:
            self.__t = t
            self.sentPerSecond = (self.__sent - self.__lastSent) / t_diff
            self.__lastSent = self.__sent

    def averageReceived(self) -> float:
        if self.__receivedCount == 0:
            return 0
        return self.__received / self.__receivedCount

    def averageSent(self) -> float:
        if self.__sentCount == 0:
            return 0
        return self.__sent / self.__sentCount


class RemoteLogger:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.host: str = host
        self.port: int = port
        self.__serverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('RemoteLogger', logLevel)
        if not os.path.exists('log'):
            os.mkdir('log')
        self.nodesIO = defaultdict(ConnectionIO)

    def run(self):
        threading.Thread(target=self.__serve).start()

    def __serve(self):
        self.__serverSocket.bind((self.host, self.port))
        self.__serverSocket.listen()
        self.logger.info('[*] serves at %s:%d over tcp.', self.host, self.port)
        while True:
            clientSocket, _ = self.__serverSocket.accept()
            threading.Thread(target=self.__receiver,
                             args=(clientSocket,)).start()

    def __receiver(self, clientSocket: socket.socket):
        buffer = b''
        payloadSize = struct.calcsize('>L')
        try:
            while True:
                while len(buffer) < payloadSize:
                    buffer += clientSocket.recv(4096)

                packedDataSize = buffer[:payloadSize]
                buffer = buffer[payloadSize:]
                dataSize = struct.unpack('>L', packedDataSize)[0]

                while len(buffer) < dataSize:
                    buffer += clientSocket.recv(4096)

                data = buffer[:dataSize]
                self.log(data, payloadSize + dataSize)
                buffer = buffer[dataSize:]
        except OSError:
            pass

    def log(self, logData, thisSize):

        message = Message.decrypt(logData)
        logList = message['logList']
        nodeName = str(message['nodeName'])

        self.nodesIO[nodeName].received(thisSize)
        self.recordIO(nodeName)
        isChangingLog = message['isChangingLog']
        isTitle = message['isTitle']

        filename = 'log@'
        filename += 'changing@' if isChangingLog else \
            'unchanging@'
        filename += '%s.csv' % nodeName
        filename = './log/' + filename
        if isTitle:
            if os.path.exists(filename):
                os.remove(filename)
            f = open(filename, 'w')
            for name in logList[:-1]:
                f.write(str(name) + ', ')
            f.write(str(logList[-1]) + '\r\n')
        else:
            with open(filename, 'a') as logFile:
                writer = csv.writer(logFile, quoting=csv.QUOTE_ALL)
                writer.writerow(logList)
                logFile.close()
        return None

    def recordIO(self, nodeName):
        nodeIO = self.nodesIO[nodeName]
        filename = './log/AverageIO@RemoteLogger@%s.csv ' % nodeName
        fileContent = 'averageReceived, averageSent, receivedPerSecond, sentPerSecond\r\n' \
                      '%f, %f, %f, %f\r\n' % (
                          nodeIO.averageReceived(),
                          nodeIO.averageSent(),
                          nodeIO.receivedPerSecond,
                          nodeIO.sentPerSecond
                      )
        self.writeFile(filename, fileContent)

    @staticmethod
    def writeFile(name, content):
        f = open(name, 'w')
        f.write(content)
        f.close()


if __name__ == '__main__':
    dataManager = RemoteLogger(host='0.0.0.0',
                               port=5001,
                               logLevel=logging.DEBUG)
    dataManager.run()
