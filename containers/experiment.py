import logging
import os
import json
from logger import get_logger
from tqdm import tqdm
from time import sleep


class Experiment:

    def __init__(self):
        self.currPath = os.path.abspath(os.path.curdir)
        self.logger = get_logger('Experiment', level_name=logging.DEBUG)

    @staticmethod
    def stopAllContainers():
        os.system('docker stop $(docker ps -a -q)')
        os.system('docker rm $(docker ps -a -q) > /dev/null 2>&1 & ')

    @staticmethod
    def runRemoteLogger():
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

    @staticmethod
    def runMaster(schedulerName):
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

    @staticmethod
    def runWorker():
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

    @staticmethod
    def runUser():
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

    @staticmethod
    def stopUser():
        os.system('docker stop '
                  '$(docker ps -a -q --filter="name=User") '
                  '> /dev/null 2>&1')

    @staticmethod
    def readRespondTime(filename):
        with open(filename) as f:
            respondTime = json.loads(f.read())
            f.close()
            os.system('rm -f %s' % filename)
            if len(respondTime):
                return list(respondTime.values())[0]
            return 0

    def removeLogs(self):
        os.system('rm -rf %s/newLogger/sources/profiler/*.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/*.json' % self.currPath)

    @staticmethod
    def runRemoteWorkers():
        os.system('ssh 4GB-rpi-4B-alpha \''
                  './runWorker.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 2GB-rpi-4B-alpha \''
                  './runWorker.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 4GB-rpi-4B-beta \''
                  './runWorker.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 2GB-rpi-4B-beta \''
                  './runWorker.sh\' '
                  '> /dev/null 2>&1 &')

    @staticmethod
    def stopRemoteWorkers():
        os.system('ssh 4GB-rpi-4B-alpha \''
                  './stopWorker.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 2GB-rpi-4B-alpha \''
                  './stopWorker.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 4GB-rpi-4B-beta \''
                  './stopWorker.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 2GB-rpi-4B-beta \''
                  './stopWorker.sh\' '
                  '> /dev/null 2>&1 &')

    @staticmethod
    def stopLocalTaskHandler():
        os.system('docker stop $(docker ps -a -q --filter="name=TaskHandler") '
                  '&& docker rm $(docker ps -a -q --filter="name=TaskHandler") '
                  '> /dev/null 2>&1')

    @staticmethod
    def stopRemoteTaskHandler():
        os.system('ssh 4GB-rpi-4B-alpha \''
                  './stopTaskHandlers.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 2GB-rpi-4B-alpha \''
                  './stopTaskHandlers.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 4GB-rpi-4B-beta \''
                  './stopTaskHandlers.sh\' '
                  '> /dev/null 2>&1 &')
        os.system('ssh 2GB-rpi-4B-beta \''
                  './stopTaskHandlers.sh\' '
                  '> /dev/null 2>&1 &')

    def rerunNecessaryContainers(self, schedulerName):
        self.stopAllContainers()
        self.stopRemoteWorkers()
        self.runRemoteLogger()
        self.runMaster(schedulerName)
        self.runWorker()
        self.runRemoteWorkers()

    def run(self, schedulerName, roundNum=None, targetRound=None):

        repeatTimes = 100
        userMaxWaitTime = 300
        respondTimeFilePath = '%s/newUser/sources/log/respondTime.json' % self.currPath
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
        sleep(1)
        while i < repeatTimes:
            self.runUser()
            # self.logger.debug('Waiting for respondTime log file to be created ...')
            sleepCount = 0
            while not os.path.exists(respondTimeFilePath):
                sleepCount += 1
                sleep(1)
                if sleepCount > userMaxWaitTime:
                    break
            self.stopUser()
            self.stopLocalTaskHandler()
            self.stopRemoteTaskHandler()
            if sleepCount > userMaxWaitTime:
                self.rerunNecessaryContainers(schedulerName)
                continue
            respondTimes[i] = self.readRespondTime(respondTimeFilePath)
            i += 1
            processBar.update(1)
            self.saveEvaluateRecord(schedulerName, roundNum, i)
            self.logger.debug('[*] Result-[%d/%d]: %s', (i + 1), repeatTimes, str(respondTimes))
        self.saveRes(schedulerName, respondTimes, roundNum)
        self.logger.info(respondTimes)

    @staticmethod
    def saveEvaluateRecord(algorithmName, roundNum, iterationNum):
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
    for num in range(targetRound_):
        experiment.run('NSGA3', num, targetRound_)
        experiment.run('NSGA2', num, targetRound_)
