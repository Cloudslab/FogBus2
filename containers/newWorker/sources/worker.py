import sys
import logging
import threading
import os
import re
import docker
import argparse
from exceptions import *
from connection import Message
from node import Node, ImagesAndContainers
from logger import get_logger


class Worker(Node):

    def __init__(
            self,
            containerName,
            myAddr,
            masterAddr,
            loggerAddr,
            logLevel=logging.DEBUG):

        self.isRegistered: threading.Event = threading.Event()
        self.dockerClient = docker.from_env()
        self.currPath = os.path.abspath(os.path.curdir)
        super().__init__(
            role='Worker',
            containerName=containerName,
            myAddr=myAddr,
            masterAddr=masterAddr,
            loggerAddr=loggerAddr,
            periodicTasks=[
                (self.__uploadImagesAndRunningContainersList, 10)],
            logLevel=logLevel
        )

    def run(self):
        self.__register()

    def __register(self):
        print('[*] Getting local available images ...')
        stats = self.container.stats(
            stream=False)
        cpuUsage = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        systemCPUUsage = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        availableMemory = stats['memory_stats']['usage']
        maxMemory = stats['memory_stats']['max_usage']
        resources = {
            'systemCPUUsage': systemCPUUsage,
            'cpuUsage': cpuUsage,
            'availableMemory': availableMemory,
            'maxMemory': maxMemory}
        message = {'type': 'register',
                   'role': 'Worker',
                   'machineID': self.machineID,
                   'resources': resources,
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
        if not role == 'Worker':
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
                command='%s %s %s %d %s %d '
                        '%d %s %s %s %s %d ' % (
                            containerName,
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
                            workerID,
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

    def __uploadResources(self):
        stats = self.container.stats(
            stream=False)
        cpuUsage = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        systemCPUUsage = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        availableMemory = stats['memory_stats']['usage']
        maxMemory = stats['memory_stats']['max_usage']
        resources = {
            'systemCPUUsage': systemCPUUsage,
            'cpuUsage': cpuUsage,
            'availableMemory': availableMemory,
            'maxMemory': maxMemory}
        msg = {
            'type': 'nodeResources',
            'resources': resources}
        self.sendMessage(msg, self.remoteLogger.addr)
        self.sendMessage(msg, self.master.addr)

    def __uploadImagesAndRunningContainersList(self):

        imagesAndContainers = ImagesAndContainers(
            images=self.__getImages(),
            containers=self.__getContainers())
        msg = {
            'type': 'imagesAndRunningContainers',
            'imagesAndRunningContainers': imagesAndContainers}
        self.sendMessage(msg, self.remoteLogger.addr)


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
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()
    worker_ = Worker(
        containerName=args.containerName,
        myAddr=(args.ip, args.port),
        masterAddr=(args.masterIP, args.masterPort),
        loggerAddr=(args.loggerIP, args.loggerPort), )
    worker_.run()
