import json
import logging
import os
import threading
from random import randint
from time import sleep
from time import time

from tqdm import tqdm

from logger import get_logger

machines = [
    '4GB-rpi-4B-alpha',
    '4GB-rpi-4B-beta',
    '2GB-rpi-4B-beta',
    '2GB-rpi-4B-alpha',
    'cloud1',
    'cloud2',
    'cloud3',
    'cloud4',
    'cloud5',
    'desktop-remote'
]
ips = {
    '4GB-rpi-4B-alpha': '10.0.0.101',
    '4GB-rpi-4B-beta': '10.0.0.102',
    '2GB-rpi-4B-beta': '10.0.0.104',
    '2GB-rpi-4B-alpha': '10.0.0.103',
    'cloud1': '10.0.0.201',
    'cloud2': '10.0.0.202',
    'cloud3': '10.0.0.203',
    'cloud4': '10.0.0.204',
    'cloud5': '10.0.0.205',
    'desktop-remote': '10.0.0.1'}

masterIP = '10.0.0.1'
minActors = len(machines)


class Experiment:

    def __init__(self):
        self.currPath = os.path.abspath(os.path.curdir)
        self.logger = get_logger('Experiment', level_name=logging.DEBUG)

    def stopAllContainers(self):
        self.logger.info(
            'Stopping all containers on where this script is running ...')
        os.system('./stopContainer.sh > /dev/null 2>&1')
        # self.logger.info('Stopped all containers on where this script is running')

    def runRemoteLogger(self):
        global masterIP
        self.logger.info('Starting RemoteLogger ...')
        os.system(
            'cd ./newLogger && '
            'docker-compose run '
            '--rm '
            '--name RemoteLogger '
            'remote_logger '
            'RemoteLogger '
            '%s 5001 '
            '%s 5000 '
            '> /dev/null 2>&1 &' % (masterIP, masterIP))
        # self.logger.info('Ran RemoteLogger')

    def runMaster(self, schedulerName, initWithLog=False):
        global masterIP, minActors
        self.logger.info('Starting Master ...')
        os.system(
            'cd ./newMaster && '
            'docker-compose run '
            '--rm '
            '--name Master '
            'master '
            'Master '
            '%s 5000 '
            '%s 5001 '
            '%s '
            '--minHosts %d '
            '%s '
            '> /dev/null 2>&1 &'
            % (
                masterIP,
                masterIP,
                schedulerName,
                minActors,
                '--initWithLog True' if initWithLog else ''))
        # self.logger.info('Ran Master')

    def runActor(self):
        global masterIP
        self.logger.info('Starting Actor ...')
        os.system(
            'cd ./newActor && '
            'docker-compose run '
            '--rm '
            '--name Actor '
            'actor '
            'Actor '
            '%s '
            '%s 5000 '
            '%s 5001 '
            '> /dev/null 2>&1 &' % (
                masterIP,
                masterIP,
                masterIP))
        self.logger.info('Ran Actor')

    def runUserGameOfLife(self):
        containerName = 'UserGoL%d' % int(time() * 1000)
        os.system(
            'cd ./newUser && '
            'docker-compose run '
            '--rm '
            '--name %s '
            'user '
            '%s '
            '%s '
            '%s 5000 '
            '%s 5001 '
            'GameOfLifePyramid '
            '128 '
            '--no-show '
            '> /dev/null 2>&1 &' % (
                containerName,
                containerName,
                masterIP,
                masterIP,
                masterIP))
        # self.logger.info('Ran Game of Life')

    def runUserOCR(self):
        # docker-compose run
        # --rm --name User
        # user User
        # 192.168.3.20
        # 192.168.3.20 5000
        # 192.168.3.20 5001
        # VideoOCR 128
        # --video video.mo4
        # --no-showWindow

        containerName = 'UserOCR%d' % int(time() * 1000)
        os.system(
            'cd ./newUser && '
            'docker-compose run '
            '--rm '
            '--name %s '
            'user '
            '%s '
            '%s '
            '%s 5000 '
            '%s 5001 '
            'VideoOCR  128 '
            '--video video.mo4 '
            '--no-showWindow '
            '> /dev/null 2>&1 &' % (
                containerName,
                containerName,
                masterIP,
                masterIP,
                masterIP))
        # self.logger.info('Ran OCR')

    def stopUser(self):
        self.logger.info('Stopping User ...')
        os.system('./stopContainer.sh User > /dev/null 2>&1')
        self.logger.info('Stopped User')

    @staticmethod
    def readResponseTime(filename):
        with open(filename, 'r') as f:
            responseTime = json.loads(f.read())
            f.close()
            os.system('rm -f %s' % filename)
            if len(responseTime):
                return list(responseTime.values())[0]
            return 0

    def removeLogs(self):
        os.system(
            'rm -rf %s/newLogger/sources/profiler/medianPackageSize.json' % self.currPath)
        os.system(
            'rm -rf %s/newLogger/sources/profiler/nodeResources.json' % self.currPath)
        os.system(
            'rm -rf %s/newLogger/sources/profiler/imagesAndRunningContainers.json' % self.currPath)
        os.system(
            'rm -rf %s/newLogger/sources/profiler/medianProcessTime.json' % self.currPath)
        os.system(
            'rm -rf %s/newLogger/sources/profiler/medianDelay.json' % self.currPath)
        os.system(
            'rm -rf %s/newLogger/sources/profiler/medianResponseTime.json' % self.currPath)
        os.system(
            'rm -rf %s/newLogger/sources/profiler/medianPackageSize.json' % self.currPath)
        os.system(
            'rm -rf %s/newMaster/sources/profiler/nodeResources.json' % self.currPath)
        os.system(
            'rm -rf %s/newMaster/sources/profiler/imagesAndRunningContainers.json' % self.currPath)
        os.system(
            'rm -rf %s/newMaster/sources/profiler/medianProcessTime.json' % self.currPath)
        os.system(
            'rm -rf %s/newMaster/sources/profiler/medianDelay.json' % self.currPath)
        os.system(
            'rm -rf %s/newMaster/sources/profiler/medianResponseTime.json' % self.currPath)

        os.system('rm -f %s/newMaster/sources/decisions.json' % self.currPath)
        self.logger.info('Removed logs')

    def stopLocalTaskExecutor(self):
        self.logger.info('Stopping local TaskExecutors ...')
        os.system('./stopContainer.sh TaskExecutor > /dev/null 2>&1')
        # self.logger.info('Stopped local TaskExecutors')

    @staticmethod
    def _sshRunScript(machine, script, event, synchronized=False):
        if synchronized:
            tmp = ''
        else:
            tmp = '&'
        if script == './runActor.sh':
            script = '%s %s %s %s' % (script, ips[machine], masterIP, masterIP)
            # print(script)
        os.system('ssh %s \'%s\' > /dev/null 2>&1 %s' % (machine, script, tmp))
        event.set()

    @staticmethod
    def manageRpi(runnable, script, synchronized=False):
        global machines
        events = [threading.Event() for _ in machines]
        for i, machine in enumerate(machines):
            threading.Thread(
                target=runnable,
                args=[machine, script, events[i], synchronized]).start()

        for event in events:
            event.wait()

    def stopRemoteTaskExecutor(self):
        self.logger.info('Stopping remote TaskExecutors ...')
        self.manageRpi(self._sshRunScript, './stopTaskExecutors.sh')
        # self.logger.info('Stopped remote TaskExecutors')

    def stopRemoteActors(self):
        self.logger.info('Stopping remote Actors ... ')
        self.manageRpi(self._sshRunScript, './stopActor.sh', synchronized=True)
        # self.logger.info('Stopped remote Actors')

    def runRemoteActors(self):
        self.logger.info('Starting remote Actors ...')
        self.manageRpi(self._sshRunScript, './runActor.sh', synchronized=True)
        # self.logger.info('Ran remote Actors')

    def rerunNecessaryContainers(self, schedulerName, initWithLog=False):
        self.stopAllContainers()
        self.stopRemoteActors()
        self.runRemoteLogger()
        self.runMaster(schedulerName, initWithLog)
        # self.runActor()
        sleep(5)
        self.runRemoteActors()
        sleep(1)

    def randomlyRunUser(self, count):
        for _ in range(count):
            sleep(0.001)
            if randint(0, 100) % 2:
                self.runUserGameOfLife()
                continue
            self.runUserOCR()

    @staticmethod
    def checkFiles(count):
        targetPath = 'newUser/sources/'
        t = [f for f in os.listdir(targetPath)
             if f.endswith('.json') and os.path.isfile(
                os.path.join(targetPath, f))]
        n = len(t)
        if n >= count:
            os.system('mv %s*.json . > /dev/null 2>&1' % targetPath)
            return True
        print('Waiting logs ... %d/%d' % (n, count), end='\r')
        return False

    @staticmethod
    def moveResultsToFolder(count):
        folderName = 'scale/%d/' % count
        if not os.path.exists(folderName):
            os.system('mkdir -p %s' % folderName)
        os.system('mv *.json %s' % folderName)

    def run(
            self,
            schedulerName,
            initWithLog,
            roundNum=None,
            targetRound=None,
            removeLog=False,
            repeatTimes=100,
            userMaxWaitTime=200):

        if removeLog:
            self.removeLogs()

        self.rerunNecessaryContainers(
            schedulerName,
            initWithLog)
        if roundNum is None:
            desc = schedulerName
        else:
            desc = '[%s-%d/%d]' % (schedulerName, roundNum, targetRound)

        i = 0
        users = [2 * i for i in range(1, 11)]
        users = [1] + users

        processBar = tqdm(
            total=repeatTimes * len(users),
            desc=desc)
        sleep(2)
        while i < repeatTimes:
            os.system('rm -rf newUser/sources/*.json > /dev/null 2>&1')
            for count in users:
                self.randomlyRunUser(count)
                sleepCount = 0
                while not self.checkFiles(count):
                    sleepCount += 1
                    sleep(1)
                    if sleepCount > userMaxWaitTime:
                        break
                    if sleepCount % 100 == 0:
                        self.randomlyRunUser(1)
                self.moveResultsToFolder(count)
                self.stopUser()
                processBar.update(1)
            i += 1


if __name__ == '__main__':
    experiment = Experiment()
    targetRound_ = 1
    repeatTimes_ = 5
    waitTime = 40
    # experiment.runInitWithLog(
    #     initWithLog=True,
    #     roundNum=targetRound_,
    #     iterNum=repeatTimes_)
    for num in range(targetRound_):
        experiment.run(
            'NSGA2',
            True,
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            removeLog=False,
            userMaxWaitTime=waitTime)
