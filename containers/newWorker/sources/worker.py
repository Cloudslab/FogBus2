import sys
import logging
import threading
import os
import re
import docker
from exceptions import *
from connection import Message
from node import Node
from logger import get_logger
from resourcesInfo import ImagesAndContainers


class Worker(Node):

    def __init__(
            self,
            myAddr,
            masterAddr,
            loggerAddr,
            coresCount,
            cpuFrequency,
            memory,
            logLevel=logging.DEBUG):

        self.isRegistered: threading.Event = threading.Event()
        self.dockerClient = docker.from_env()
        self.currPath = os.path.abspath(os.path.curdir)
        super().__init__(
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            coresCount=coresCount,
            cpuFrequency=cpuFrequency,
            memory=memory,
            periodicTasks=[
                (self.__uploadImagesAndRunningContainersList, 10)],
            logLevel=logLevel
        )

    def run(self):
        self.__register()

    def __register(self):
        print('[*] Getting local available images ...')
        message = {'type': 'register',
                   'role': 'worker',
                   'machineID': self.machineID,
                   'resources': self.resources.all(),
                   'images': self.__getImages()}
        self.sendMessage(message, self.master.addr)
        self.isRegistered.wait()
        self.logger.info("Registered.")

    def handleMessage(self, message: Message):
        if self.isMessage(message, 'registered'):
            self.__handleRegistered(message)
        elif self.isMessage(message, 'runTaskHandler'):
            self.__handleRunTaskHandler(message)

    def __handleRegistered(self, message: Message):
        role = message.content['role']
        if not role == 'worker':
            raise RegisteredAsWrongRole
        self.id = message.content['id']
        self.role = role
        self.setName(message)
        self.logger = get_logger(self.nameLogPrinting, self.logLevel)
        self.isRegistered.set()

    def __handleRunTaskHandler(self, message: Message):
        userID = message.content['userID']
        userName = message.content['userName']
        taskName = message.content['taskName']
        token = message.content['token']
        childTaskTokens = message.content['childTaskTokens']
        workerID = self.id
        try:
            containerName = '%s_%s_%s' % (taskName, userName.replace('@', ''), self.nameLogPrinting)
            for container in self.dockerClient.containers.list():
                if container.name != containerName:
                    continue
                return
            self.dockerClient.containers.run(
                name=containerName,
                detach=True,
                auto_remove=True,
                image=self.camel_to_snake(taskName),
                network_mode='host',
                working_dir='/workplace',
                command='%s %s %d %s %d '
                        '%d %s %s %s %s %d' % (
                            self.myAddr[0],
                            self.masterAddr[0],
                            self.masterAddr[1],
                            self.loggerAddr[0],
                            self.loggerAddr[1],
                            userID,
                            userName,
                            taskName,
                            token,
                            ','.join(childTaskTokens) if len(childTaskTokens) else 'None',
                            workerID
                        )
            )
            self.logger.info('Ran %s', taskName)
        except docker.errors.APIError as e:
            self.logger.warning(str(e))


    @staticmethod
    def snake_to_camel(snake_str):
        if snake_str == 'oct':
            return 'OCR'
        # https://stackoverflow.com/questions/19053707
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)

    @staticmethod
    def camel_to_snake(name):
        # https://stackoverflow.com/questions/1175208
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def __getImages(self):
        imagesList = self.dockerClient.images.list()

        imageNames = set()
        for image in imagesList:
            tags = image.tags
            if not len(tags):
                continue
            imageNames.add(self.snake_to_camel(tags[0].split(':')[0]))
        return imageNames

    def __getContainers(self):
        containerList = self.dockerClient.containers.list()

        runningContainers = set()
        for container in containerList:
            tags = container.image.tags
            if not len(tags):
                continue
            runningContainers.add(self.snake_to_camel(tags[0].split(':')[0]))
        return runningContainers

    def __uploadImagesAndRunningContainersList(self):

        imagesAndContainers = ImagesAndContainers(
            images=self.__getImages(),
            containers=self.__getContainers())
        msg = {
            'type': 'imagesAndRunningContainers',
            'imagesAndRunningContainers': imagesAndContainers}
        self.sendMessage(msg, self.remoteLogger.addr)


if __name__ == '__main__':
    myAddr_ = (sys.argv[1], int(sys.argv[2]))
    masterAddr_ = (sys.argv[3], int(sys.argv[4]))
    loggerAddr_ = (sys.argv[5], int(sys.argv[6]))
    if len(sys.argv) > 7:
        coresCount_ = sys.argv[7]
        if ',' in coresCount_:
            coresCount_ = len(coresCount_.split(','))
        elif '-' in coresCount_:
            start, end = coresCount_.split('-')
            coresCount_ = int(end) - int(start) + 1
        else:
            coresCount_ = 1
        cpuFrequency_ = int(sys.argv[8])
        memory_ = sys.argv[0]
    else:
        memory_ = None
        coresCount_ = None
        cpuFrequency_ = None
    worker_ = Worker(
        myAddr=myAddr_,
        masterAddr=masterAddr_,
        loggerAddr=loggerAddr_,
        coresCount=coresCount_,
        cpuFrequency=cpuFrequency_,
        memory=memory_)
    worker_.run()
