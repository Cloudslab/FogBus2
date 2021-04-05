import argparse
import os
from logging import DEBUG

from utils import Address
from utils import BasicComponent
from utils import ComponentRole
from utils import ConfigUser
from utils import ContainerManager
from utils import MessageSubType
from utils import MessageType
from utils import PeriodicTaskRunner
from utils import PeriodicTasks
from utils import ResourcesDiscovery
from utils.user import initActuator
from utils.user import RegistrationManager
from utils.user import UserMessageHandler
from utils.user import WindowManager


class User:

    def __init__(
            self,
            addr: Address,
            masterAddr: Address,
            remoteLoggerAddr: Address,
            appName: str,
            showWindow: bool,
            label: str,
            videoPath: str,
            golInitText: str,
            containerName: str = '',
            logLevel=DEBUG):
        self.containerName = containerName
        self.basicComponent = BasicComponent(
            role=ComponentRole.USER,
            addr=addr,
            masterAddr=masterAddr,
            remoteLoggerAddr=remoteLoggerAddr,
            logLevel=logLevel,
            portRange=ConfigUser.portRange)
        self.resourcesDiscovery = ResourcesDiscovery(
            basicComponent=self.basicComponent)
        self.discoverIfUnset()
        self.containerManager = ContainerManager(
            basicComponent=self.basicComponent,
            containerName=containerName)
        self.registrationManager = RegistrationManager(
            basicComponent=self.basicComponent,
            appName=appName,
            label=label)
        self.actuator = initActuator(
            appName=appName,
            label=self.registrationManager.label,
            videoPath=videoPath,
            showWindow=showWindow,
            basicComponent=self.basicComponent,
            golInitText=golInitText)
        if self.actuator is None:
            self.basicComponent.debugLogger.error(
                'Application is not supported: %s',
                self.registrationManager.appName)
            os._exit(0)

        self.messageHandler = UserMessageHandler(
            resourcesDiscovery=self.resourcesDiscovery,
            containerManager=self.containerManager,
            basicComponent=self.basicComponent,
            actuator=self.actuator,
            registrationManager=self.registrationManager)
        periodicTasks = self.preparePeriodTasks()
        self.periodicTaskRunner = PeriodicTaskRunner(
            basicComponent=self.basicComponent,
            periodicTasks=periodicTasks)

    def discoverIfUnset(self):
        remoteLogger = self.basicComponent.remoteLogger
        if remoteLogger.addr[0] == '' or remoteLogger.addr[1] == 0:
            self.resourcesDiscovery.discoverAndCommunicate(
                targetRole=ComponentRole.REMOTE_LOGGER,
                isNotSetInArgs=True)
        master = self.basicComponent.master
        if master.addr[0] == '' or master.addr[1] == 0:
            self.resourcesDiscovery.discoverAndCommunicate(
                targetRole=ComponentRole.MASTER,
                isNotSetInArgs=True)
        self.resourcesDiscovery.checkPorts()

    def run(self):
        self.register()
        if not self.actuator.showWindow:
            return
        windowManager = WindowManager(
            basicComponent=self.basicComponent,
            frameQueue=self.actuator.windowFrameQueue,
            prepareWindows=self.actuator.prepare,
            pressSpaceToStart=self.actuator.pressSpaceToStart,
            canStart=self.actuator.canStart)
        windowManager.run()

    def register(self):
        self.registrationManager.registerAt(self.basicComponent.master.addr)

    def uploadMedianResponseTime(self):
        responseTime = self.actuator.responseTime.median()
        if responseTime == 0:
            return
        data = {'responseTime': responseTime}
        self.basicComponent.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.RESPONSE_TIME,
            data=data,
            destination=self.basicComponent.remoteLogger)

    def preparePeriodTasks(self) -> PeriodicTasks:
        periodicTasks = [(self.uploadMedianResponseTime, 10)]
        return periodicTasks


def parseArg():
    parser = argparse.ArgumentParser(
        description='User')
    parser.add_argument(
        '--bindIP',
        metavar='BindIP',
        type=str,
        help='User ip.')
    parser.add_argument(
        '--bindPort',
        metavar='BindPort',
        nargs='?',
        default=0,
        type=int,
        help='Bind port')
    parser.add_argument(
        '--masterIP',
        metavar='MasterIP',
        type=str,
        help='Master ip.')
    parser.add_argument(
        '--masterPort',
        metavar='MasterPort',
        nargs='?',
        default=0,
        type=int,
        help='Master port')
    parser.add_argument(
        '--remoteLoggerIP',
        metavar='RemoteLoggerIP',
        type=str,
        help='Remote logger ip.')
    parser.add_argument(
        '--remoteLoggerPort',
        metavar='RemoteLoggerPort',
        nargs='?',
        default=0,
        type=int,
        help='Remote logger port')
    parser.add_argument(
        '--applicationName',
        metavar='ApplicationName',
        type=str,
        help='Application Name')
    parser.add_argument(
        '--applicationLabel',
        metavar='ApplicationLabel',
        default=480,
        type=int,
        help='e.g. 480 or 720')

    parser.add_argument(
        '--containerName',
        metavar='ContainerName',
        nargs='?',
        default='',
        type=str,
        help='container name')
    parser.add_argument(
        '--videoPath',
        metavar='VideoPath',
        nargs='?',
        default=0,
        type=str,
        help='/path/to/video.mp4')
    parser.add_argument(
        '--showWindow',
        metavar='ShowWindow',
        default=True,
        action=argparse.BooleanOptionalAction,
        help='Show window or not')
    parser.add_argument(
        '--verbose',
        metavar='Verbose',
        nargs='?',
        default=10,
        type=int,
        help='Reference python logging level, from 0 to 50 integer to show log')
    parser.add_argument(
        '--golInitText',
        metavar='GameOfLifeInitialWorldText',
        nargs='?',
        default='Qifan Deng',
        type=str,
        help='GameOfLife initial world text')
    return parser.parse_args()


if __name__ == "__main__":
    args = parseArg()
    user_ = User(
        containerName=args.containerName,
        addr=(args.bindIP, args.bindPort),
        masterAddr=(args.masterIP, args.masterPort),
        remoteLoggerAddr=(args.remoteLoggerIP, args.remoteLoggerPort),
        appName=args.applicationName,
        label=args.applicationLabel,
        showWindow=args.showWindow,
        videoPath=args.videoPath,
        golInitText=args.golInitText,
        logLevel=args.verbose)
    user_.run()
