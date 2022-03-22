from os import system
from time import time
from typing import List
from typing import Tuple

from docker.client import DockerClient
from docker.errors import APIError

from .base import BaseInitiator
from ...component.basic import BasicComponent
from ...tools import camelToSnake
from ...tools import filterIllegalCharacter
from ...types import CPU


class TaskExecutorInitiator(BaseInitiator):

    def __init__(
            self,
            basicComponent: BasicComponent,
            isContainerMode: bool,
            dockerClient: DockerClient,
            cpu: CPU):
        BaseInitiator.__init__(
            self,
            basicComponent=basicComponent,
            isContainerMode=isContainerMode,
            dockerClient=dockerClient)
        self.cpu = cpu

    def initTaskExecutor(
            self,
            userID: str,
            userName: str,
            taskName: str,
            taskToken: str,
            childTaskTokens: List[str],
            isContainerMode: bool):
        baseTaskName, label = self.covertTaskName(taskName)
        actor = self.basicComponent.me
        master = self.basicComponent.master
        remoteLogger = self.basicComponent.remoteLogger
        childTaskTokens = self.serialize(childTaskTokens)
        args = ' --bindIP %s' % actor.addr[0] + \
               ' --masterIP %s' % master.addr[0] + \
               ' --masterPort %d' % master.addr[1] + \
               ' --remoteLoggerIP %s' % remoteLogger.addr[0] + \
               ' --remoteLoggerPort %d' % remoteLogger.addr[1] + \
               ' --userID %s' % userID + \
               ' --taskName %s' % baseTaskName + \
               ' --taskToken %s' % taskToken + \
               ' --childrenTaskTokens %s' % childTaskTokens + \
               ' --actorID %s' % actor.componentID + \
               ' --totalCPUCores %d' % self.cpu.cores + \
               ' --cpuFrequency %f' % self.cpu.frequency + \
               ' --verbose %d' % self.basicComponent.debugLogger.level
        if not isContainerMode:
            self.initTaskExecutorOnHost(args=args)
            return

        containerName = '%s_%s_%s_%s' % (
            taskName,
            userName,
            actor.nameLogPrinting,
            time())
        containerName = filterIllegalCharacter(string=containerName)
        args += ' --containerName %s' % containerName
        imageName = 'fogbus2-%s' % camelToSnake(baseTaskName)
        self.initTaskExecutorInContainer(
            imageName=imageName, containerName=containerName, args=args)

    def initTaskExecutorOnHost(self, args: str):
        system('cd ../../taskExecutor/sources/ &&'
               ' python taskExecutor.py %s &' % args)
        self.basicComponent.debugLogger.debug(
            'Init TaskExecutor on host:\n %s', args)

    def initTaskExecutorInContainer(
            self, args: str, imageName: str, containerName: str):
        try:
            self.dockerClient.containers.run(
                name=containerName,
                detach=True,
                auto_remove=True,
                image=imageName,
                network_mode='host',
                working_dir='/workplace',
                volumes={
                    '/var/run/docker.sock':
                        {
                            'bind': '/var/run/docker.sock',
                            'mode': 'rw'}},
                command=args)
            self.basicComponent.debugLogger.debug(
                'Init TaskExecutor in container:\n%s', args)
        except APIError as e:
            if 'cloudslab/' != imageName[:10]:
                return self.initTaskExecutorInContainer(
                    args=args,
                    imageName='cloudslab/'+imageName,
                    containerName=containerName)
            self.basicComponent.debugLogger.warning(str(e))

    @staticmethod
    def serialize(childrenTaskTokens: List[str]) -> str:
        if not len(childrenTaskTokens):
            return 'None'
        return ','.join(childrenTaskTokens)

    @staticmethod
    def covertTaskName(taskName: str) -> Tuple[str, str]:
        dashIndex = taskName.find('-')
        if dashIndex == -1:
            label = 'None'
        else:
            label = taskName[dashIndex:]
        baseTaskName = taskName[:dashIndex]
        return baseTaskName, label
