import argparse
import logging
from time import sleep

from utils import BasicComponent
from utils import ComponentRole
from utils import ConfigMaster
from utils import ContainerManager
from utils import DiscoveredMasters
from utils import MessageSubSubType
from utils import MessageSubType
from utils import MessageType
from utils import PeriodicTaskRunner
from utils import PeriodicTasks
from utils import terminate
from utils.master import ApplicationManager
from utils.master import initSchedulerByName
from utils.master import LoggerManager
from utils.master import MasterMessageHandler
from utils.master import MasterProfiler
from utils.master import MasterResourcesDiscovery
from utils.master import Registry


class Master:

    def __init__(
            self,
            addr,
            masterAddr,
            remoteLoggerAddr,
            schedulerName: str,
            createdByIP: str,
            createdByPort: int,
            minActors: int,
            netGateway: str = '',
            subnetMask: str = '255.255.255.0',
            databaseType: str = 'MariaDB',
            logLevel=logging.DEBUG,
            containerName: str = '',
            parsedArgs=None,
            waitTimeout: int = 0):
        self.parsedArgs = parsedArgs

        self.basicComponent = BasicComponent(
            role=ComponentRole.MASTER,
            addr=addr,
            masterAddr=masterAddr,
            remoteLoggerAddr=remoteLoggerAddr,
            logLevel=logLevel,
            ignoreSocketError=True,
            portRange=ConfigMaster.portRange)

        self.loggerManager = LoggerManager(basicComponent=self.basicComponent)
        self.containerManager = ContainerManager(
            basicComponent=self.basicComponent,
            containerName=containerName)
        self.applicationManager = ApplicationManager(
            databaseType=databaseType
        )
        self.profiler = MasterProfiler(
            basicComponent=self.basicComponent,
            loggerManager=self.loggerManager,
            minActors=minActors)
        discoveredMasters = DiscoveredMasters()
        self.scheduler = initSchedulerByName(
            knownMasters=discoveredMasters,
            minimumActors=minActors,
            schedulerName=schedulerName,
            populationSize=200,
            generationNum=100,
            basicComponent=self.basicComponent,
            parsedArgs=parsedArgs,
            isContainerMode=self.containerManager.isContainerMode)
        if self.scheduler is None:
            self.basicComponent.debugLogger.error(
                'Scheduler name is invalid: %s', schedulerName)
            terminate()
        self.registry = Registry(
            basicComponent=self.basicComponent,
            applicationManager=self.applicationManager,
            scheduler=self.scheduler,
            systemPerformance=self.loggerManager.systemPerformance,
            profiler=self.profiler,
            waitTimeout=waitTimeout)
        self.resourcesDiscovery = MasterResourcesDiscovery(
            registry=self.registry,
            basicComponent=self.basicComponent,
            subnetMask=subnetMask,
            netGateway=netGateway,
            createdByIP=createdByIP,
            createdByPort=createdByPort)
        self.resourcesDiscovery.discovered.masters = discoveredMasters
        self.discoverIfUnset()
        self.messageHandler = MasterMessageHandler(
            basicComponent=self.basicComponent,
            registry=self.registry,
            loggerManager=self.loggerManager,
            profiler=self.profiler,
            resourcesDiscovery=self.resourcesDiscovery)
        periodicTasks = self.preparePeriodTasks()
        self.periodicTaskRunner = PeriodicTaskRunner(
            basicComponent=self.basicComponent,
            periodicTasks=periodicTasks)

    def discoverIfUnset(self):
        remoteLogger = self.basicComponent.remoteLogger
        if remoteLogger.addr[0] == '' or remoteLogger.addr[1] == 0:
            self.resourcesDiscovery.discoverAndCommunicate(
                targetRole=ComponentRole.REMOTE_LOGGER)

    def run(self):
        self.containerManager.tryRenamingContainerName(
            newName=self.basicComponent.nameLogPrinting)
        # if this Master was created by another
        if self.resourcesDiscovery.isScaled:
            createdBy = self.resourcesDiscovery.createdBy
            self.basicComponent.debugLogger.info(
                'Was created by %s', str(createdBy.addr))
            self.resourcesDiscovery.requestLoggerFrom(createdBy)
            self.basicComponent.sendMessage(
                messageType=MessageType.RESOURCE_DISCOVERY,
                messageSubType=MessageSubType.PROBE,
                messageSubSubType=MessageSubSubType.RESULT,
                data={'role': ComponentRole.MASTER.value},
                destination=createdBy)
            self.profiler.dataRateTestEvent.set()
        else:
            self.basicComponent.debugLogger.debug(
                'Waiting for %s actors',self.profiler.minHosts)
            while len(self.registry.registeredManager.actors) < \
                    self.profiler.minHosts:
                sleep(1)
            self.profiler.gotEnoughActors.set()
            self.basicComponent.debugLogger.debug(
                'There are %s actors registered',
                len(self.registry.registeredManager.actors))
        self.basicComponent.debugLogger.info("Serving...")

    def preparePeriodTasks(self) -> PeriodicTasks:
        periodicTasks = [
            (self.uploadDataRate, 30),
            (self.profiler.periodicallyProfileDataRate,
             self.parsedArgs.profileDataRatePeriod),
            (self.uploadLatency, 30),
            (self.updateResources, 30),
            (self.profiler.loggerManager.saveAll, 1800),
            (self.profiler.loggerManager.retrieveAll, 1900),
            (self.uploadProfiles, 2000),
            (self.requestProfiler, 2100),
            # (self.resourcesDiscovery.discoverMasters, 3600 * 3),
            # (self.resourcesDiscovery.discoverActors, 3600 * 3),
            # (self.resourcesDiscovery.getActorAddrFromOtherMasters, 3200),
            (self.resourcesDiscovery.advertiseMeToActors, 3300)]
        return periodicTasks

    def uploadDataRate(self):
        data = {
            'dataRate': self.profiler.loggerManager.systemPerformance.dataRate}
        self.basicComponent.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.DATA_RATE_TEST,
            messageSubSubType=MessageSubSubType.RESULT,
            data=data,
            destination=self.basicComponent.remoteLogger)
        self.profiler.registeredActors = self.registry.registeredManager.actors

    def uploadLatency(self):
        data = {
            'latency': self.profiler.loggerManager.systemPerformance.latency}
        self.basicComponent.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.LATENCY,
            messageSubSubType=MessageSubSubType.RESULT,
            data=data,
            destination=self.basicComponent.remoteLogger)

    def uploadProfiles(self):
        data = {'profiles': self.profiler.loggerManager.toDict()}
        self.basicComponent.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.PROFILES,
            data=data,
            destination=self.basicComponent.remoteLogger)

    def updateResources(self):
        self.profiler.me.profileResources()

    def requestProfiler(self):
        self.basicComponent.sendMessage(
            messageType=MessageType.LOG,
            messageSubType=MessageSubType.REQUEST_PROFILES,
            data={},
            destination=self.basicComponent.remoteLogger)


def parseArg():
    parser = argparse.ArgumentParser(
        description='Master')
    parser.add_argument(
        '--bindIP',
        metavar='BindIP',
        type=str,
        help='Master ip.')
    parser.add_argument(
        '--bindPort',
        metavar='ListenPort',
        nargs='?',
        default=0,
        type=int,
        help='Master port.')
    parser.add_argument(
        '--remoteLoggerIP',
        metavar='RemoteLoggerIP',
        nargs='?',
        default='',
        type=str,
        help='Remote logger ip.')
    parser.add_argument(
        '--remoteLoggerPort',
        metavar='RemoteLoggerPort',
        nargs='?',
        type=int,
        default=0,
        help='Remote logger port')
    parser.add_argument(
        '--schedulerName',
        metavar='SchedulerName',
        nargs='?',
        default='OHNSGA',
        type=str,
        help='Scheduler name')
    parser.add_argument(
        '--createdByIP',
        metavar='CreatedByIP',
        nargs='?',
        default='',
        type=str,
        help='IP of the Master who asked to create this new Master')
    parser.add_argument(
        '--createdByPort',
        metavar='CreatedByPort',
        nargs='?',
        default=0,
        type=int,
        help='Port of the Master who asked to create this new Master')
    parser.add_argument(
        '--minimumActors',
        metavar='MinimumActors',
        default=1,
        type=int,
        help='minimum actors needed')
    parser.add_argument(
        '--estimationThreadNum',
        metavar='EstimationThreadNumber',
        nargs='?',
        default=4,
        type=int,
        help='Estimation thread number')
    parser.add_argument(
        '--databaseType',
        metavar='DatabaseType',
        nargs='?',
        default='MariaDB',
        type=str,
        help='Database type, e.g., MariaDB')
    parser.add_argument(
        '--verbose',
        metavar='Verbose',
        nargs='?',
        default=10,
        type=int,
        help='Reference python logging level, from 0 to 50 integer to show log')
    parser.add_argument(
        '--profileDataRatePeriod',
        metavar='ProfileDataRatePeriod',
        nargs='?',
        default=24 * 3600,
        type=int,
        help='Period for Master to profile data rate and latency. In seconds. '
             'Set to 0 to disable')
    parser.add_argument(
        '--taskExecutorCoolPeriod',
        metavar='TaskExecutorCoolPeriod (Reusability)',
        nargs='?',
        default=0,
        type=int,
        help='How many seconds does task executor wait after finishes task')
    parser.add_argument(
        '--containerName',
        metavar='ContainerName',
        nargs='?',
        default='',
        type=str,
        help='container name')

    return parser.parse_args()


if __name__ == '__main__':
    args_ = parseArg()
    master_ = Master(
        containerName=args_.containerName,
        addr=(args_.bindIP, args_.bindPort),
        masterAddr=(args_.bindIP, args_.bindPort),
        remoteLoggerAddr=(args_.remoteLoggerIP, args_.remoteLoggerPort),
        schedulerName=args_.schedulerName,
        createdByIP=args_.createdByIP,
        createdByPort=args_.createdByPort,
        minActors=args_.minimumActors,
        databaseType=args_.databaseType,
        parsedArgs=args_,
        logLevel=args_.verbose)
    master_.run()
