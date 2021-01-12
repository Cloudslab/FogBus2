import logging
import threading
import struct
import socket
import csv
import os
from logger import get_logger
from message import Message


class RemoteLogger:

    def __init__(self, host: str, port: int, logLevel=logging.DEBUG):
        self.host: str = host
        self.port: int = port
        self.__serverSocket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = get_logger('RemoteLogger', logLevel)
        if not os.path.exists('remoteLog'):
            os.mkdir('remoteLog')

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
                self.log(data)
                buffer = buffer[dataSize:]
        except OSError:
            pass

    @staticmethod
    def log(logData):
        message = Message.decrypt(logData)
        logList = message['logList']
        nodeName = str(message['nodeName'])
        isChangingLog = message['isChangingLog']
        isTitle = message['isTitle']

        filename = 'changing_' if isChangingLog else \
            'unchanging_'
        filename += nodeName
        filename = './remoteLog/' + filename
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


if __name__ == '__main__':
    dataManager = RemoteLogger(host='0.0.0.0',
                               port=5001,
                               logLevel=logging.DEBUG)
    dataManager.run()
