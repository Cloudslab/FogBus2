from os import system
from time import time

from docker.client import DockerClient
from docker.errors import APIError
from .base import BaseInitiator
from ...component.basic import BasicComponent
from ...tools import filterIllegalCharacter,encrypt
from ...types import Component
from ...types import ActorResources


class ActorInitiator(BaseInitiator):

    def __init__(
            self,
            basicComponent: BasicComponent,
            isContainerMode: bool,
            dockerClient: DockerClient):
        BaseInitiator.__init__(
            self,
            basicComponent=basicComponent,
            dockerClient=dockerClient,
            isContainerMode=isContainerMode)

    def initActor(
            self,
            me: Component,
            master: Component,
            remoteLogger: Component,
            isContainerMode: bool):
        args = ' --bindIP %s' % me.addr[0] + \
               ' --masterIP %s' % master.addr[0] + \
               ' --masterPort %d' % master.addr[1] + \
               ' --remoteLoggerIP %s' % remoteLogger.addr[0] + \
               ' --remoteLoggerPort %d' % remoteLogger.addr[1] + \
               ' --verbose %d' % self.basicComponent.debugLogger.level
        if not isContainerMode:
            self.initActorOnHost(args=args)
            return
        containerName = filterIllegalCharacter(string='Actor_%f' % time())
        args += ' --containerName %s' % containerName
        imageName = 'fogbus2-actor'
        self.initActorInContainer(
            imageName=imageName, containerName=containerName, args=args)
        return

    def initActorOnHost(self, args: str):
        system('cd ../../actor/sources/ && python actor.py %s &' % args)
        self.basicComponent.debugLogger.debug('Init Actor on host:\n%s', args)

    def initActorInContainer(
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
                'Init Actor in container:\n%s', args)
        except APIError as e:
            self.basicComponent.debugLogger.warning(str(e))
