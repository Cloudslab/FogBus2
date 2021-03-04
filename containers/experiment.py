import logging
import os
import json
import threading
from logger import get_logger
from tqdm import tqdm
from time import sleep


class Experiment:

    def __init__(self):
        self.currPath = os.path.abspath(os.path.curdir)
        self.logger = get_logger('Experiment', level_name=logging.DEBUG)

    def stopAllContainers(self):
        self.logger.info('Stopping all containers on where this script is running ...')
        os.system('./stopContainer.sh > /dev/null 2>&1')
        # self.logger.info('Stopped all containers on where this script is running')

    def runRemoteLogger(self):
        self.logger.info('Starting RemoteLogger ...')
        os.system(
            'cd ./newLogger && '
            'docker-compose run '
            '--rm '
            '--name RemoteLogger '
            'remote-logger '
            'RemoteLogger '
            '192.168.3.20 5001 '
            '192.168.3.20 5000 '
            '> /dev/null 2>&1 &')
        # self.logger.info('Ran RemoteLogger')

    def runMaster(self, schedulerName):
        self.logger.info('Starting Master ...')
        os.system(
            'cd ./newMaster && '
            'docker-compose run '
            '--rm '
            '--name Master '
            'master '
            'Master '
            '192.168.3.20 5000 '
            '192.168.3.20 5001 '
            '%s '
            '> /dev/null 2>&1 &' % schedulerName)
        # self.logger.info('Ran Master')

    def runWorker(self):
        self.logger.info('Starting Worker ...')
        os.system(
            'cd ./newWorker && '
            'docker-compose run '
            '--rm '
            '--name Worker '
            'worker '
            'Worker '
            '192.168.3.20 '
            '192.168.3.20 5000 '
            '192.168.3.20 5001 '
            '> /dev/null 2>&1 &')
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
            '192.168.3.20 '
            '192.168.3.20 5000 '
            '192.168.3.20 5001 '
            'GameOfLifePyramid '
            '256 '
            '--no-show '
            '> /dev/null 2>&1 &')
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
        os.system('rm -rf %s/newLogger/sources/profiler/*.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/*.json' % self.currPath)
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
        os.system('ssh %s \'%s\' > /dev/null 2>&1 %s' % (machine, script, tmp))
        event.set()

    @staticmethod
    def manageRpi(runnable, script, synchronized=False):
        machines = [
            '4GB-rpi-4B-alpha',
            '2GB-rpi-4B-alpha',
            '4GB-rpi-4B-beta',
            '2GB-rpi-4B-beta']
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
        self.manageRpi(self._sshRunScript, './runWorker.sh')
        # self.logger.info('Ran remote Workers')

    def rerunNecessaryContainers(self, schedulerName):
        self.stopAllContainers()
        self.stopRemoteWorkers()
        self.runRemoteLogger()
        self.runMaster(schedulerName)
        self.runWorker()
        self.runRemoteWorkers()
        sleep(1)

    def run(
            self,
            schedulerName,
            roundNum=None,
            targetRound=None,
            repeatTimes=100,
            userMaxWaitTime=200):
        respondTimeFilePath = '%s/newUser/sources/log/respondTime.json' % self.currPath
        os.system('rm -f %s > /dev/null 2>&1' % respondTimeFilePath)
        respondTimes = [0 for _ in range(repeatTimes)]

        self.removeLogs()
        self.rerunNecessaryContainers(schedulerName)
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
            respondTimes[i] = self.readRespondTime(respondTimeFilePath)
            self.saveEstimatedRecord(schedulerName, roundNum, i)
            i += 1
            processBar.update(1)
            self.logger.info('[*] Result-[%d/%d]: %s', i, repeatTimes, str(respondTimes))
            self.stopLocalTaskHandler()
            self.stopRemoteTaskHandler()
        self.saveRes(schedulerName, respondTimes, roundNum)
        self.logger.info(respondTimes)

    @staticmethod
    def saveEstimatedRecord(algorithmName, roundNum, iterationNum):
        os.system('mv '
                  './newMaster/sources/record.json '
                  './Evaluation-%s-%d-%d.json' % (algorithmName, roundNum, iterationNum))

    @staticmethod
    def saveRes(schedulerName, respondTimes, roundNum):
        if roundNum is None:
            filename = '%s.json' % schedulerName
        else:
            filename = '%s-%d.json' % (schedulerName, roundNum)
        with open(filename, 'w+') as f:
            json.dump(respondTimes, f)
            f.close()


if __name__ == '__main__':
    experiment = Experiment()
    targetRound_ = 10
    repeatTimes_ = 100
    waitTime = 180
    for num in range(targetRound_):
        experiment.run(
            'NSGA3',
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            userMaxWaitTime=waitTime)
        experiment.run(
            'NSGA2',
            num + 1,
            targetRound_,
            repeatTimes=repeatTimes_,
            userMaxWaitTime=waitTime)
