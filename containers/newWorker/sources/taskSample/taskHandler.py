import logging
import threading
import argparse
from exceptions import *
from connection import Message, Median
from node import Node
from logger import get_logger
from typing import List, Dict
from time import sleep, time
from apps import *


class TaskHandler(Node):

    def __init__(
            self,
            containerName,
            myAddr,
            masterAddr,
            loggerAddr,
            userID: int,
            userName: str,
            taskName: str,
            token: str,
            childTaskTokens: List[str],
            workerID: int,
            totalCPUCores: int,
            cpuFreq: float,
            logLevel=logging.DEBUG):

        self.userID: int = userID
        self.userName: str = userName
        self.taskName: str = taskName
        self.token: str = token
        self.childTaskTokens: List[str] = childTaskTokens
        self.workerID: int = workerID
        self.isRegistered: threading.Event = threading.Event()
        self.childrenAddr: Dict[str, tuple] = {}
        self.processTime: Median = Median()
        self.totalCPUCores = totalCPUCores
        self.cpuFreq = cpuFreq

        super().__init__(
            role='TaskHandler',
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadMedianProcessTime, 20)],
            logLevel=logLevel
        )

        app = None
        if taskName == 'FaceDetection':
            app = FaceDetection()
        elif taskName == 'EyeDetection':
            app = EyeDetection()
        elif taskName == 'ColorTracking':
            app = ColorTracking()
        elif taskName == 'BlurAndPHash':
            app = BlurAndPHash()
        elif taskName == 'OCR':
            app = OCR()
        elif taskName == 'GameOfLife0':
            app = GameOfLife0()
        elif taskName == 'GameOfLife1':
            app = GameOfLife1()
        elif taskName == 'GameOfLife2':
            app = GameOfLife2()
        elif taskName == 'GameOfLife3':
            app = GameOfLife3()
        elif taskName == 'GameOfLife4':
            app = GameOfLife4()
        elif taskName == 'GameOfLife5':
            app = GameOfLife5()
        elif taskName == 'GameOfLife6':
            app = GameOfLife6()
        elif taskName == 'GameOfLife7':
            app = GameOfLife7()
        elif taskName == 'GameOfLife8':
            app = GameOfLife8()
        elif taskName == 'GameOfLife9':
            app = GameOfLife9()
        elif taskName == 'GameOfLife10':
            app = GameOfLife10()
        elif taskName == 'GameOfLife11':
            app = GameOfLife11()
        elif taskName == 'GameOfLife12':
            app = GameOfLife12()
        elif taskName == 'GameOfLife13':
            app = GameOfLife13()
        elif taskName == 'GameOfLife14':
            app = GameOfLife14()
        elif taskName == 'GameOfLife15':
            app = GameOfLife15()
        elif taskName == 'GameOfLife16':
            app = GameOfLife16()
        elif taskName == 'GameOfLife17':
            app = GameOfLife17()
        elif taskName == 'GameOfLife18':
            app = GameOfLife18()
        elif taskName == 'GameOfLife19':
            app = GameOfLife19()
        elif taskName == 'GameOfLife20':
            app = GameOfLife20()
        elif taskName == 'GameOfLife21':
            app = GameOfLife21()
        elif taskName == 'GameOfLife22':
            app = GameOfLife22()
        elif taskName == 'GameOfLife23':
            app = GameOfLife23()
        elif taskName == 'GameOfLife24':
            app = GameOfLife24()
        elif taskName == 'GameOfLife25':
            app = GameOfLife25()
        elif taskName == 'GameOfLife26':
            app = GameOfLife26()
        elif taskName == 'GameOfLife27':
            app = GameOfLife27()
        elif taskName == 'GameOfLife28':
            app = GameOfLife28()
        elif taskName == 'GameOfLife29':
            app = GameOfLife29()
        elif taskName == 'GameOfLife30':
            app = GameOfLife30()
        elif taskName == 'GameOfLife31':
            app = GameOfLife31()
        elif taskName == 'GameOfLife32':
            app = GameOfLife32()
        elif taskName == 'GameOfLife33':
            app = GameOfLife33()
        elif taskName == 'GameOfLife34':
            app = GameOfLife34()
        elif taskName == 'GameOfLife35':
            app = GameOfLife35()
        elif taskName == 'GameOfLife36':
            app = GameOfLife36()
        elif taskName == 'GameOfLife37':
            app = GameOfLife37()
        elif taskName == 'GameOfLife38':
            app = GameOfLife38()
        elif taskName == 'GameOfLife39':
            app = GameOfLife39()
        elif taskName == 'GameOfLife40':
            app = GameOfLife40()
        elif taskName == 'GameOfLife41':
            app = GameOfLife41()
        elif taskName == 'GameOfLife42':
            app = GameOfLife42()
        elif taskName == 'GameOfLife43':
            app = GameOfLife43()
        elif taskName == 'GameOfLife44':
            app = GameOfLife44()
        elif taskName == 'GameOfLife45':
            app = GameOfLife45()
        elif taskName == 'GameOfLife46':
            app = GameOfLife46()
        elif taskName == 'GameOfLife47':
            app = GameOfLife47()
        elif taskName == 'GameOfLife48':
            app = GameOfLife48()
        elif taskName == 'GameOfLife49':
            app = GameOfLife49()
        elif taskName == 'GameOfLife50':
            app = GameOfLife50()
        elif taskName == 'GameOfLife51':
            app = GameOfLife51()
        elif taskName == 'GameOfLife52':
            app = GameOfLife52()
        elif taskName == 'GameOfLife53':
            app = GameOfLife53()
        elif taskName == 'GameOfLife54':
            app = GameOfLife54()
        elif taskName == 'GameOfLife55':
            app = GameOfLife55()
        elif taskName == 'GameOfLife56':
            app = GameOfLife56()
        elif taskName == 'GameOfLife57':
            app = GameOfLife57()
        elif taskName == 'GameOfLife58':
            app = GameOfLife58()
        elif taskName == 'GameOfLife59':
            app = GameOfLife59()
        elif taskName == 'GameOfLife60':
            app = GameOfLife60()
        elif taskName == 'GameOfLife61':
            app = GameOfLife61()
        if app is None:
            msg = {
                'type': 'exit',
                'reason': 'No TaskHandler named %s' % taskName}
            self.sendMessage(msg, self.master.addr)
        else:
            self.app: TasksWorkerSide = app

    def __uploadMedianProcessTime(self):
        if self.processTime.median() is None:
            return
        msg = {
            'type': 'medianProcessTime',
            'medianProcessTime': (
                self.processTime.median(),
                self.totalCPUCores,
                self.cpuFreq)}
        self.sendMessage(msg, self.remoteLogger.addr)

    def run(self):
        self.__register()
        self.__lookupChildren()

    def __register(self):
        message = {
            'type': 'register',
            'role': 'TaskHandler',
            'userID': self.userID,
            'taskName': self.taskName,
            'workerID': self.workerID,
            'token': self.token,
            'machineID': self.machineID}
        self.sendMessage(message, self.master.addr)
        self.isRegistered.wait()
        self.logger.info("Registered.")

    def __lookupChildren(self):
        while True:
            if len(self.childTaskTokens) == len(self.childrenAddr.keys()):
                break
            for childToken in self.childTaskTokens:
                if childToken in self.childrenAddr:
                    continue
                msg = {'type': 'lookup', 'token': childToken}
                self.sendMessage(msg, self.master.addr)
            sleep(1)
        msg = {'type': 'ready', 'token': self.token}
        self.sendMessage(msg, self.master.addr)
        self.logger.info('Got %d children\'s addr' % len(self.childTaskTokens))

    def handleMessage(self, message: Message):
        if message.type == 'registered':
            self.__handleRegistered(message)
        elif message.type == 'taskHandlerInfo':
            self.__handleTaskHandlerInfo(message)
        elif message.type == 'data':
            self.__handleData(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'TaskHandler':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.role = role
        self.setName(message)
        self.machineID = message.content['workerMachineID']
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.isRegistered.set()

    def __handleTaskHandlerInfo(self, message: Message):
        taskHandlerAddr = message.content['addr']
        taskHandlerToken = message.content['token']
        if taskHandlerToken not in self.childTaskTokens:
            return
        self.childrenAddr[taskHandlerToken] = taskHandlerAddr

        if not len(self.childTaskTokens) == len(self.childrenAddr.keys()):
            return
        msg = {'type': 'ready', 'token': self.token}
        self.sendMessage(msg, self.master.addr)

    def __handleData(self, message: Message):
        data = message.content['data']
        result = self.app.process(data)
        self.processTime.update((time() * 1000 - message.content['_receivedAt']))
        if result is None:
            return

        msg = message.content
        if len(self.childrenAddr.keys()):
            msg['data'] = result
            for token, addr in self.childrenAddr.items():
                try:
                    self.sendMessage(msg, addr)
                except OSError:
                    msg = {'type': 'exit', 'reason': 'Cannot connect to %s' % token}
                    self.sendMessage(msg, self.master.addr)
            return

        del msg['data']
        msg['type'] = 'result'
        msg['result'] = result

        self.sendMessage(msg, self.master.addr)


def parseArg():
    parser = argparse.ArgumentParser(
        description='User'
    )
    parser.add_argument(
        'containerName',
        metavar='ContainerName',
        type=str,
        help='Current container name, used for getting runtime usages.'
    )
    parser.add_argument(
        'ip',
        metavar='BindIP',
        type=str,
        help='User ip.'
    )
    parser.add_argument(
        'masterIP',
        metavar='MasterIP',
        type=str,
        help='Master ip.'
    )
    parser.add_argument(
        'masterPort',
        metavar='MasterPort',
        type=int,
        help='Master port'
    )
    parser.add_argument(
        'loggerIP',
        metavar='RemoteLoggerIP',
        type=str,
        help='Remote logger ip.'
    )
    parser.add_argument(
        'loggerPort',
        metavar='RemoteLoggerPort',
        type=int,
        help='Remote logger port'
    )
    parser.add_argument(
        'userID',
        metavar='UserID',
        type=int,
        help='User id.'
    )
    parser.add_argument(
        'userName',
        metavar='UserName',
        type=str,
        help='User name.'
    )
    parser.add_argument(
        'taskName',
        metavar='TaskName',
        type=str,
        help='Task name.'
    )
    parser.add_argument(
        'token',
        metavar='Token',
        type=str,
        help='Task token.'
    )
    parser.add_argument(
        'childTaskTokens',
        metavar='ChildTaskTokens',
        type=str,
        help='Children task token. E.g. token0,token1,token2'
    )
    parser.add_argument(
        'workerID',
        metavar='WorkerID',
        type=int,
        help='Worker id.'
    )
    parser.add_argument(
        'totalCPUCores',
        metavar='TotalCPUCores',
        type=int,
        help='cpu cores count'
    )
    parser.add_argument(
        'cpuFreq',
        metavar='CPUFreq',
        type=float,
        help='cpu frequency'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()

    if args.childTaskTokens == 'None':
        args.childTaskTokens = []
    else:
        args.childTaskTokens = args.childTaskTokens.split(',')

    taskHandler_ = TaskHandler(
        containerName=args.containerName,
        myAddr=(args.ip, 0),
        masterAddr=(args.masterIP, args.masterPort),
        loggerAddr=(args.loggerIP, args.loggerPort),
        userID=args.userID,
        userName=args.userName,
        taskName=args.taskName,
        token=args.token,
        childTaskTokens=args.childTaskTokens,
        workerID=args.workerID,
        totalCPUCores=args.totalCPUCores,
        cpuFreq=args.cpuFreq)

    taskHandler_.run()
