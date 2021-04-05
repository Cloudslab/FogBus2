import json
import logging
import os
import threading
from time import sleep

from tqdm import tqdm

from logger import get_logger

machines = [
    '4GB-rpi-4B-alpha',
    '4GB-rpi-4B-beta',
    '2GB-rpi-4B-beta',
    '2GB-rpi-4B-alpha',
    'cloud1',
    'cloud2',
    'desktop-remote'
]
ips = {
    '4GB-rpi-4B-alpha': '10.0.0.101',
    '4GB-rpi-4B-beta': '10.0.0.102',
    '2GB-rpi-4B-beta': '10.0.0.104',
    '2GB-rpi-4B-alpha': '10.0.0.103',
    'cloud1': '10.0.0.201',
    'cloud2': '10.0.0.202',
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
            'Actor '
            'Actor '
            '%s '
            '%s 5000 '
            '%s 5001 '
            '> /dev/null 2>&1 &' % (
                masterIP,
                masterIP,
                masterIP))
        self.logger.info('Ran Actor')

    def runUser(self):
        self.logger.info('Starting User ...')
        os.system(
            'cd ./newUser && '
            'docker-compose run '
            '--rm '
            '--name User '
            'user '
            'User '
            '%s '
            '%s 5000 '
            '%s 5001 '
            'GameOfLifePyramid '
            '128 '
            '--no-show '
            '> /dev/null 2>&1 &' % (
                masterIP,
                masterIP,
                masterIP))
        self.logger.info('Ran User')

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
            print(script)
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

    def run(
            self,
            schedulerName,
            initWithLog,
            roundNum=None,
            targetRound=None,
            removeLog=False,
            repeatTimes=100,
            userMaxWaitTime=200):
        responseTimeFilePath = '%s/newUser/sources/log/responseTime.json' % self.currPath
        os.system('rm -f %s > /dev/null 2>&1' % responseTimeFilePath)
        responseTimes = [0 for _ in range(repeatTimes)]

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
        processBar = tqdm(
            total=repeatTimes,
            desc=desc)
        sleep(2)
        while i < repeatTimes:
            self.runUser()
            # self.logger.debug('Waiting for responseTime log file to be created ...')
            sleepCount = 0
            while not os.path.exists(responseTimeFilePath):
                sleepCount += 1
                sleep(1)
                if sleepCount > userMaxWaitTime:
                    break
            if sleepCount > userMaxWaitTime:
                self.rerunNecessaryContainers(schedulerName)
                continue
            self.stopUser()
            responseTimes[i] = self.readResponseTime(
                responseTimeFilePath)
            self.saveEstimatedRecord(
                schedulerName,
                roundNum,
                i,
                initWithLog)
            i += 1
            processBar.update(1)
            self.logger.info('[*] Result-[%d/%d]: %s', i, repeatTimes,
                             str(responseTimes))
            self.stopLocalTaskExecutor()
            self.stopRemoteTaskExecutor()
        self.saveRes(
            schedulerName,
            responseTimes,
            roundNum,
            initWithLog=initWithLog)
        self.logger.info(responseTimes)

    def runInitWithLog(
            self,
            initWithLog,
            roundNum,
            iterNum):
        schedulerName = 'NSGA2'
        recordPath = './newMaster/sources/record.json'
        os.system('rm -f %s' % recordPath)
        self.rerunNecessaryContainers(
            schedulerName,
            initWithLog)
        sleep(2)
        for i in tqdm(range(iterNum)):
            self.runUser()
            while not os.path.exists(recordPath):
                sleep(1)
            self.saveEstimatedRecord(
                schedulerName,
                roundNum,
                i,
                initWithLog=initWithLog)
            self.stopUser()
        self.logger.info('Done init with log')

    @staticmethod
    def saveEstimatedRecord(
            algorithmName,
            roundNum,
            iterationNum,
            initWithLog=False):
        os.system('mv '
                  './newMaster/sources/record.json '
                  './Evaluation-%s-%d-%d.json' % (
                      '%s%s' % (
                          algorithmName,
                          'InitWithLog' if initWithLog else ''),
                      roundNum,
                      iterationNum))

    @staticmethod
    def saveRes(
            schedulerName,
            responseTimes,
            roundNum,
            initWithLog):
        fix = 'InitWithLog' if initWithLog else ''
        if roundNum is None:
            filename = '%s.json' % schedulerName
        else:
            filename = '%s%s-%d.json' % (
                schedulerName,
                fix,
                roundNum)
        with open(filename, 'w+') as f:
            json.dump(responseTimes, f)
            f.close()


if __name__ == '__main__':
    experiment = Experiment()
    targetRound_ = 1
    repeatTimes_ = 100
    waitTime = 300
    # experiment.runInitWithLog(
    #     initWithLog=True,
    #     roundNum=targetRound_,
    #     iterNum=repeatTimes_)
    for num in range(targetRound_):
        # experiment.run(
        #     'NSGA3',
        #     False,
        #     num + 1,
        #     targetRound_,
        #     repeatTimes=repeatTimes_,
        #     removeLog=True,
        #     userMaxWaitTime=waitTime)
        experiment.run(
            'NSGA2',
            True,
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            removeLog=False,
            userMaxWaitTime=waitTime)
        # experiment.run(
        #     'NSGA2',
        #     False,
        #     num + 1,
        #     targetRound_,
        #     repeatTimes=repeatTimes_,
        #     removeLog=True,
        #     userMaxWaitTime=waitTime)
