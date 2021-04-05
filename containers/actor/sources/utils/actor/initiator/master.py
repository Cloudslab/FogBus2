from os import system
from time import time

from docker.errors import APIError

from .base import BaseInitiator
from ...connection.message import MessageReceived
from ...tools import filterIllegalCharacter
from ...types import ComponentIdentity


class MasterInitiator(BaseInitiator):

    def initMaster(
            self,
            me: ComponentIdentity,
            createdBy: ComponentIdentity,
            remoteLogger: ComponentIdentity,
            message: MessageReceived,
            isContainerMode: bool):
        data = message.data
        schedulerName = data['schedulerName']
        minimumActors = data['minimumActors']
        estimationThreadNum = data['estimationThreadNum']
        # try to create a Master

        args = ' --bindIP %s' % me.addr[0] + \
               ' --remoteLoggerIP %s' % remoteLogger.addr[0] + \
               ' --remoteLoggerPort %d' % remoteLogger.addr[1] + \
               ' --schedulerName %s' % schedulerName + \
               ' --createdByIP %s' % createdBy.addr[0] + \
               ' --createdByPort %d' % createdBy.addr[1] + \
               ' --minimumActors %d' % minimumActors + \
               ' --estimationThreadNum %d' % estimationThreadNum + \
               ' --verbose %d' % self.basicComponent.debugLogger.level

        if not isContainerMode:
            self.initMasterOnHost(args=args)
            return

        containerName = filterIllegalCharacter(string='Master_%f' % time())
        args += ' --containerName %s' % containerName
        imageName = 'fogbus2-master'
        self.initMasterInContainer(
            imageName=imageName, containerName=containerName, args=args)

    def initMasterOnHost(self, args: str):
        system('cd ../../master/sources/ && python master.py %s &' % args)
        self.basicComponent.debugLogger.debug('Init Master on host:\n%s', args)

    def initMasterInContainer(
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
                'Init Master in container:\n%s', args)
        except APIError as e:
            self.basicComponent.debugLogger.warning(str(e))
