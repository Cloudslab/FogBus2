import logging
import os
import json
import threading
from logger import get_logger
from tqdm import tqdm
from time import sleep

machines = [
    '4GB-rpi-4B-alpha',
    '2GB-rpi-4B-alpha',
    '2GB-rpi-4B-beta',
    'uniCloud1',
    'uniCloud2'
]
ips = {
    '4GB-rpi-4B-alpha': '10.0.0.101',
    '2GB-rpi-4B-alpha': '10.0.0.103',
    '2GB-rpi-4B-beta': '10.0.0.104',
    'uniCloud1': '10.0.0.2',
    'uniCloud2': '10.0.0.3'
}

masterIP = '10.0.0.101'
minWorkers = len(machines)


class Experiment:

    def __init__(self):
        self.currPath = os.path.abspath(os.path.curdir)
        self.logger = get_logger('Experiment', level_name=logging.DEBUG)

    def stopAllContainers(self):
        self.logger.info('Stopping all containers on where this script is running ...')
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
            'remote-logger '
            'RemoteLogger '
            '%s 5001 '
            '%s 5000 '
            '> /dev/null 2>&1 &' % (masterIP, masterIP))
        # self.logger.info('Ran RemoteLogger')

    def runMaster(self, schedulerName, initWithLog=False):
        global masterIP, minWorkers
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
            '--minHosts %d'
            '%s '
            '> /dev/null 2>&1 &'
            % (
                masterIP,
                masterIP,
                schedulerName,
                minWorkers,
                '--initWithLog True' if initWithLog else ''))
        # self.logger.info('Ran Master')

    def runWorker(self):
        global masterIP
        self.logger.info('Starting Worker ...')
        os.system(
            'cd ./newWorker && '
            'docker-compose run '
            '--rm '
            '--name Worker '
            'worker '
            'Worker '
            '%s '
            '%s 5000 '
            '%s 5001 '
            '> /dev/null 2>&1 &' % (
                masterIP,
                masterIP,
                masterIP
            ))
        self.logger.info('Ran Worker')

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
                masterIP
            ))
        self.logger.info('Ran User')

    def stopUser(self):
        self.logger.info('Stopping User ...')
        os.system('./stopContainer.sh User > /dev/null 2>&1')
        self.logger.info('Stopped User')

    @staticmethod
    def readRespondTime(filename):
        with open(filename, 'r') as f:
            respondTime = json.loads(f.read())
            f.close()
            os.system('rm -f %s' % filename)
            if len(respondTime):
                return list(respondTime.values())[0]
            return 0

    def removeLogs(self):
        os.system('rm -rf %s/newLogger/sources/profiler/medianPackageSize.json' % self.currPath)
        os.system('rm -rf %s/newLogger/sources/profiler/nodeResources.json' % self.currPath)
        os.system('rm -rf %s/newLogger/sources/profiler/imagesAndRunningContainers.json' % self.currPath)
        os.system('rm -rf %s/newLogger/sources/profiler/medianProcessTime.json' % self.currPath)
        os.system('rm -rf %s/newLogger/sources/profiler/medianDelay.json' % self.currPath)
        os.system('rm -rf %s/newLogger/sources/profiler/medianRespondTime.json' % self.currPath)
        os.system('rm -rf %s/newLogger/sources/profiler/medianPackageSize.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/nodeResources.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/imagesAndRunningContainers.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/medianProcessTime.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/medianDelay.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/medianRespondTime.json' % self.currPath)

        os.system('rm -f %s/newMaster/sources/decisions.json' % self.currPath)
        self.logger.info('Removed logs')

    def stopLocalTaskHandler(self):
        self.logger.info('Stopping local TaskHandlers ...')
        os.system('./stopContainer.sh TaskHandler > /dev/null 2>&1')
        # self.logger.info('Stopped local TaskHandlers')

    @staticmethod
    def _sshRunScript(machine, script, event, synchronized=False):
        if synchronized:
            tmp = ''
        else:
            tmp = '&'
        if script == './runWorker.sh':
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

    def stopRemoteTaskHandler(self):
        self.logger.info('Stopping remote TaskHandlers ...')
        self.manageRpi(self._sshRunScript, './stopTaskHandlers.sh')
        # self.logger.info('Stopped remote TaskHandlers')

    def stopRemoteWorkers(self):
        self.logger.info('Stopping remote Workers ... ')
        self.manageRpi(self._sshRunScript, './stopWorker.sh', synchronized=True)
        # self.logger.info('Stopped remote Workers')

    def runRemoteWorkers(self):
        self.logger.info('Starting remote Workers ...')
        self.manageRpi(self._sshRunScript, './runWorker.sh', synchronized=True)
        # self.logger.info('Ran remote Workers')

    def rerunNecessaryContainers(self, schedulerName, initWithLog=False):
        self.stopAllContainers()
        self.stopRemoteWorkers()
        self.runRemoteLogger()
        self.runMaster(schedulerName, initWithLog)
        self.runWorker()
        sleep(5)
        self.runRemoteWorkers()
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
        respondTimeFilePath = '%s/newUser/sources/log/respondTime.json' % self.currPath
        os.system('rm -f %s > /dev/null 2>&1' % respondTimeFilePath)
        respondTimes = [0 for _ in range(repeatTimes)]

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
            # self.logger.debug('Waiting for respondTime log file to be created ...')
            sleepCount = 0
            while not os.path.exists(respondTimeFilePath):
                sleepCount += 1
                sleep(1)
                if sleepCount > userMaxWaitTime:
                    break
            if sleepCount > userMaxWaitTime:
                self.rerunNecessaryContainers(schedulerName)
                continue
            self.stopUser()
            respondTimes[i] = self.readRespondTime(
                respondTimeFilePath)
            self.saveEstimatedRecord(
                schedulerName,
                roundNum,
                i,
                initWithLog)
            i += 1
            processBar.update(1)
            self.logger.info('[*] Result-[%d/%d]: %s', i, repeatTimes, str(respondTimes))
            self.stopLocalTaskHandler()
            self.stopRemoteTaskHandler()
        self.saveRes(
            schedulerName,
            respondTimes,
            roundNum,
            initWithLog=initWithLog)
        self.logger.info(respondTimes)

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
                initWithLog=initWithLog
            )
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
            respondTimes,
            roundNum,
            initWithLog):
        fix = 'InitWithLog' if initWithLog else ''
        if roundNum is None:
            filename = '%s.json' % schedulerName
        else:
            filename = '%s%s-%d.json' % (
                fix,
                schedulerName,
                roundNum)
        with open(filename, 'w+') as f:
            json.dump(respondTimes, f)
            f.close()


if __name__ == '__main__':
    experiment = Experiment()
    targetRound_ = 5
    repeatTimes_ = 100
    waitTime = 300
    # experiment.runInitWithLog(
    #     initWithLog=True,
    #     roundNum=targetRound_,
    #     iterNum=repeatTimes_)
    for num in range(targetRound_):
        experiment.run(
            'NSGA2',
            False,
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            removeLog=True,
            userMaxWaitTime=waitTime)
        experiment.run(
            'NSGA3',
            False,
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            removeLog=True,
            userMaxWaitTime=waitTime)
        experiment.run(
            'NSGA2',
            True,
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            removeLog=True,
            userMaxWaitTime=waitTime)
