import argparse
from logging import DEBUG
from time import sleep

from utils import newDebugLogger
from utils import RemoteHost


class Demo:

    def __init__(self, logLevel: int = DEBUG):
        self.debugLogger = newDebugLogger(
            loggerName='Demo',
            levelName=logLevel)
        self.parser = prepareParser()

        self.args = self.parser.parse_args()

    def run(self):
        specifiedArg = False
        proxy = self.args.buildProxy
        if self.args.buildRemoteLoggerImage or self.args.buildAll:
            specifiedArg = True
            from utils import RemoteLoggerImageBuilder
            remoteLoggerImageBuilder = RemoteLoggerImageBuilder()
            self.debugLogger.info('Building RemoteLogger Image...')
            remoteLoggerImageBuilder.build(
                proxy=proxy,
                platforms=self.args.platforms,
                dockerHubUsername=self.args.dockerHubUsername,
                push=self.args.push)
        if self.args.buildMasterImage or self.args.buildAll:
            specifiedArg = True
            from utils import MasterImageBuilder
            masterImageBuilder = MasterImageBuilder()
            self.debugLogger.info('Building Master Image...')
            masterImageBuilder.build(
                proxy=proxy,
                platforms=self.args.platforms,
                dockerHubUsername=self.args.dockerHubUsername,
                push=self.args.push)
        if self.args.buildActorImage or self.args.buildAll:
            specifiedArg = True
            from utils import ActorImageBuilder
            actorImageBuilder = ActorImageBuilder()
            self.debugLogger.info('Building Actor Image...')
            actorImageBuilder.build(
                proxy=proxy,
                platforms=self.args.platforms,
                dockerHubUsername=self.args.dockerHubUsername,
                push=self.args.push)
        if self.args.buildTaskExecutorImage or self.args.buildAll:
            specifiedArg = True
            from utils import TaskExecutorImageBuilder
            taskExecutorImageBuilder = TaskExecutorImageBuilder()
            self.debugLogger.info('Building TaskExecutor Image...')
            taskExecutorImageBuilder.build(
                proxy=proxy,
                platforms=self.args.platforms,
                dockerHubUsername=self.args.dockerHubUsername,
                push=self.args.push)
        if self.args.buildUserImage or self.args.buildAll:
            specifiedArg = True
            from utils import UserImageBuilder
            userImageBuilder = UserImageBuilder()
            self.debugLogger.info('Building User Image...')
            userImageBuilder.build(
                proxy=proxy,
                platforms=self.args.platforms,
                dockerHubUsername=self.args.dockerHubUsername,
                push=self.args.push)

        if self.args.default:
            specifiedArg = True
            self.default()
        if specifiedArg:
            self.debugLogger.info('Demo finished')
        else:
            self.parser.print_help()

    def prepareRemote(self) -> RemoteHost:
        self.debugLogger.info('Username for SSH:')
        user = input()
        if user == '':
            user = 'ubuntu'
        self.debugLogger.info('Host for SSH:')
        host = input()
        if host == '':
            host = '192.168.3.49'
        self.debugLogger.info('Port for SSH:')
        port = input()
        if port == '':
            port = 22
        else:
            port = int(port)
        remoteHost = RemoteHost(user=user, host=host, port=port)
        if self.args.uploadCode:
            remoteHost.uploadCode()
        if self.args.buildRemoteImages:
            remoteHost.buildImages()
        return remoteHost

    def default(self):
        if self.args.withRPi or self.args.onlyRPi:
            remoteHost = self.prepareRemote()

        bindIP = self.args.bindIP
        verbose = self.args.verbose

        from utils import RemoteLoggerRunner
        remoteLogger = RemoteLoggerRunner()
        args = ' --bindIP %s ' % bindIP + \
               '--bindPort 5000' \
               ' --verbose %d' % verbose
        remoteLogger.run(args=args)
        sleep(5)

        from utils import MasterRunner
        master = MasterRunner()
        args = ' --bindIP %s' % bindIP + \
               ' --bindPort 5001' \
               ' --remoteLoggerIP %s' % bindIP + \
               ' --remoteLoggerPort 5000' \
               ' --verbose %d' % verbose
        master.run(args=args)
        sleep(5)
        if not self.args.onlyRPi:
            from utils import ActorRunner
            actor = ActorRunner()
            args = ' --bindIP %s ' % bindIP + \
                   ' --masterIP %s' % bindIP + \
                   ' --masterPort 5001' \
                   ' --remoteLoggerIP %s' % bindIP + \
                   ' --remoteLoggerPort 5000' \
                   ' --verbose %d' % verbose
            actor.run(args=args)
        if self.args.withRPi or self.args.onlyRPi:
            remoteHost.runActor(hostIP=bindIP)
        sleep(5)
        from utils import UserRunner
        user = UserRunner()
        self.runApp(user, self.args.applicationName, bindIP, verbose)
        # self.runExperiment(user, bindIP, verbose)

    def runExperiment(self, user, bindIP, verbose):
        # apps = ['FaceDetection', 'FaceAndEyeDetection', 'ColorTracking',
        #         'GameOfLifePyramid', 'VideoOCR']
        apps = ['GameOfLifeParallelized']
        for appName in apps:
            self.runApp(user, appName, bindIP, verbose)
            sleep(5)
            for _ in range(5):
                self.runApp(user, appName, bindIP, verbose)

    def runApp(self, user, appName, bindIP, verbose):
        appLabel = self.args.applicationLabel
        videoPath = self.args.videoPath
        args = ' --bindIP %s' \
               ' --masterIP %s' \
               ' --masterPort 5001' \
               ' --remoteLoggerIP %s' \
               ' --remoteLoggerPort 5000' \
               ' --verbose %d' \
               ' --applicationName %s' \
               ' --applicationLabel %d' \
               ' --videoPath %s' % (
                   bindIP,
                   bindIP,
                   bindIP,
                   verbose,
                   appName,
                   appLabel,
                   videoPath)
        if not self.args.showWindow:
            args += ' --no-showWindow'
        user.run(args=args)


def prepareParser():
    parser = argparse.ArgumentParser(
        description='Demo')
    parser.add_argument(
        '--buildProxy',
        metavar='BuildProxy',
        nargs='?',
        default=None,
        type=str,
        help='Proxy used when building images')
    parser.add_argument(
        '--buildAll',
        metavar='BuildAllImage',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build images of'
             ' RemoteLogger, Master, Actor, TaskExecutor, and User')
    parser.add_argument(
        '--buildActorImage',
        metavar='BuildActorImage',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build Actor image or not')
    parser.add_argument(
        '--buildMasterImage',
        metavar='BuildMasterImage',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build Master image or not')
    parser.add_argument(
        '--buildUserImage',
        metavar='BuildUserImage',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build User image or not')
    parser.add_argument(
        '--buildRemoteLoggerImage',
        metavar='BuildRemoteLoggerImage',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build RemoteLogger image or not')
    parser.add_argument(
        '--buildTaskExecutorImage',
        metavar='BuildTaskExecutorImage',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build TaskExecutor image or not')
    parser.add_argument(
        '--default',
        metavar='DefaultDemo',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Run default demonstration with all components running locally.'
             'Showing FaceAndEyeDetection and 1 container each component.')
    parser.add_argument(
        '--applicationName',
        metavar='ApplicationName',
        type=str,
        default='FaceAndEyeDetection',
        help='Application Name')
    parser.add_argument(
        '--applicationLabel',
        metavar='ApplicationLabel',
        type=int,
        default=480,
        help='e.g. 480 or 720')
    parser.add_argument(
        '--videoPath',
        metavar='VideoPath',
        default=0,
        type=str,
        help='/path/to/video.mp4')
    parser.add_argument(
        '--platforms',
        metavar='Platforms',
        default='',
        type=str,
        help='If you want to build images for cross platforms, set your '
             'platforms here.'
             'E.g., linux/amd64,linux/arm64,linux/arm/v7,linux/arm/v6. '
             'You may need to run the following before it: \n'
             'docker run --privileged --rm tonistiigi/binfmt --install all')
    parser.add_argument(
        '--dockerHubUsername',
        metavar='DockerHubUsername',
        default='',
        type=str,
        help='If you want to push built images to your docker hub, set your '
             'docker hub username here. Otherwise, leave it to be empty string')
    parser.add_argument(
        '--showWindow',
        metavar='ShowWindow',
        default=True,
        action=argparse.BooleanOptionalAction,
        help='Show window or not')
    parser.add_argument(
        '--uploadCode',
        metavar='UploadCode',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Upload Code to RPi or not')
    parser.add_argument(
        '--buildRemoteImages',
        metavar='BuildRemoteImages',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Build images on RPi or not')
    parser.add_argument(
        '--withRPi',
        metavar='WithRPi',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Demo with Raspberry Pi or not')
    parser.add_argument(
        '--onlyRPi',
        metavar='OnlyRPi',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Demo only with Raspberry Pi')
    parser.add_argument(
        '--push',
        metavar='Push',
        default=False,
        action=argparse.BooleanOptionalAction,
        help='Push images to Docker Hub or not')
    parser.add_argument(
        '--bindIP',
        metavar='BindIP',
        nargs='?',
        type=str,
        default='127.0.0.1',
        help='Which IP to use')
    parser.add_argument(
        '--verbose',
        metavar='Verbose',
        nargs='?',
        default=20,
        type=int,
        help='Reference python logging level, from 0 to 50 integer to show log')

    return parser


if __name__ == '__main__':
    demo = Demo()
    demo.run()
