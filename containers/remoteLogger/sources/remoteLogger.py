from argparse import ArgumentParser
from logging import DEBUG

from utils import Address
from utils import BasicComponent
from utils import ComponentRole
from utils import ConfigRemoteLogger
from utils import ContainerManager
from utils import PeriodicTaskRunner
from utils import PeriodicTasks
from utils import ResourcesDiscovery
from utils.remoteLogger import LoggerManager
from utils.remoteLogger import RemoteLoggerMessageHandler


class RemoteLogger:
    def __init__(
            self,
            addr: Address,
            logLevel=DEBUG,
            containerName: str = ''):
        self.basicComponent = BasicComponent(
            role=ComponentRole.REMOTE_LOGGER,
            addr=addr,
            logLevel=logLevel,
            masterAddr=('0.0.0.0', 0),
            remoteLoggerAddr=addr,
            ignoreSocketError=True,
            portRange=ConfigRemoteLogger.portRange)
        self.basicComponent.remoteLogger = self.basicComponent.me
        self.loggerManager = LoggerManager(
            basicComponent=self.basicComponent)
        self.resourcesDiscovery = ResourcesDiscovery(
            basicComponent=self.basicComponent)
        self.messageHandler = RemoteLoggerMessageHandler(
            resourcesDiscovery=self.resourcesDiscovery,
            basicComponent=self.basicComponent,
            loggerManager=self.loggerManager)
        self.containerManager = ContainerManager(
            basicComponent=self.basicComponent,
            containerName=containerName)
        periodicTasks = self.preparePeriodTasks()
        self.periodicTaskRunner = PeriodicTaskRunner(
            basicComponent=self.basicComponent,
            periodicTasks=periodicTasks)

    def run(self):
        self.loggerManager.retrieveAll()
        self.containerManager.tryRenamingContainerName(
            newName=self.basicComponent.nameLogPrinting)
        self.basicComponent.debugLogger.info('Running ...')

    def preparePeriodTasks(self) -> PeriodicTasks:
        periodicTasks = [
            # get all logs from database half an hour
            # in case of other components uploaded any
            (self.loggerManager.saveAll, 10),
            (self.loggerManager.retrieveAll, 10),
        ]
        return periodicTasks


def parseArg():
    parser = ArgumentParser(
        description='Remote Logger')
    parser.add_argument(
        '--bindIP',
        metavar='BindIP',
        type=str,
        help='Remote logger ip.')
    parser.add_argument(
        '--bindPort',
        metavar='ListenPort',
        nargs='?',
        default=0,
        type=int,
        help='Remote logger port.')
    parser.add_argument(
        '--verbose',
        metavar='Verbose',
        nargs='?',
        default=10,
        type=int,
        help='Reference python logging level, from 0 to 50 integer to show log')
    parser.add_argument(
        '--containerName',
        metavar='ContainerName',
        nargs='?',
        default='',
        type=str,
        help='container name')
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArg()
    remoteLogger_ = RemoteLogger(
        addr=(args.bindIP, args.bindPort),
        containerName=args.containerName,
        logLevel=args.verbose)
    remoteLogger_.run()
