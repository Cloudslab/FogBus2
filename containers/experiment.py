import logging
import threading
import docker
import os
import json
from logger import get_logger
from tqdm import tqdm
from typing import List
from time import sleep


class Experiment:

    def __init__(self):
        self.currPath = os.path.abspath(os.path.curdir)
        self.client = docker.from_env()
        self.logger = get_logger('Experiment', level_name=logging.DEBUG)

    def stopAllContainers(self):
        # os.system('docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)')
        try:
            containerList = self.client.containers.list()
        except Exception:
            self.stopAllContainers()
            return
        events: List[threading.Event] = [threading.Event() for _ in range(len(containerList))]
        for i, container in enumerate(containerList):
            self.stopContainer(container, events[i])
        for event in tqdm(
                events,
                desc='Stopping Running Containers',
                unit='container'):
            event.wait()

    def stopContainer(self, container, event):
        threading.Thread(
            target=self.__stopContainer,
            args=(container, event)).start()

    @staticmethod
    def __stopContainer(container, event):
        # self.logger.info('[*] Stopping %s ...', container.name)
        try:
            container.stop()
        except Exception:
            pass
        # self.logger.info('[*] Stopped %s ...', container.name)
        event.set()

    def _run(self, **kwargs):
        return self.client.containers.run(
            detach=True,
            auto_remove=True,
            network_mode='host',
            working_dir='/workplace',
            **kwargs)

    def runRemoteLogger(self):
        return self._run(
            name='RemoteLogger',
            image='remote-logger',
            volumes={
                '%s/newLogger/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'}
            },
            command='192.168.3.20 5001 '
                    '192.168.3.20 5000 '
                    '192.168.3.20 5001')

    def runMaster(self, schedulerName):
        return self._run(
            name='Master',
            image='master',
            volumes={
                '%s/newMaster/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'}
            },
            command='192.168.3.20 5000 '
                    '192.168.3.20 5000 '
                    '192.168.3.20 5001 '
                    '%s' % schedulerName)

    def runWorker(self, core: str, cpuFreq: int, mem: str, name: str):
        return self._run(
            name=name,
            image='worker',
            cpuset_cpus=core,
            cpu_period=cpuFreq,
            mem_limit=mem,
            volumes={
                '%s/newWorker/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'},
                '/var/run/docker.sock': {
                    'bind': '/var/run/docker.sock',
                    'mode': 'rw'}
            },
            command='192.168.3.20 0 '
                    '192.168.3.20 5000 '
                    '192.168.3.20 5001 '
                    '%s %s %s' % (core, cpuFreq, mem))

    def runWorkers(self, config):
        cores = config['cores']
        cpuFrequencies = config['cpuFrequencies']
        memories = config['memories']
        workers = [None for _ in range(len(cores))]
        for i in range(len(cores)):
            core = cores[i]
            freq = cpuFrequencies[i]
            mem = memories[i]
            workers[i] = self.runWorker(core, freq, mem, 'Worker-%d' % (i + 1))
        return workers

    def runUser(self, name):
        return self._run(
            name=name,
            image='user',
            volumes={
                '%s/newUser/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'}
            },
            command='192.168.3.20 '
                    '192.168.3.20 5000 '
                    '192.168.3.20 5001 '
                    'GameOfLifePyramid '
                    'noshow '
                    '256')

    @staticmethod
    def readRespondTime():
        filename = 'newUser/sources/log/respondTime.json'
        with open(filename) as f:
            respondTime = json.loads(f.read())
            f.close()
            if len(respondTime):
                return list(respondTime.values())[0]
            return 0

    def removeLogs(self):
        os.system('rm -rf %s/newLogger/sources/profiler/*.json' % self.currPath)
        os.system('rm -rf %s/newMaster/sources/profiler/*.json' % self.currPath)

    @staticmethod
    def runRemoteWorkers():
        os.system('ssh 4GB-rpi-4B \'cd new/containers/newWorker '
                  '&& docker-compose run --rm worker '
                  '192.168.3.49 5002 '
                  '192.168.3.20 5000 '
                  '192.168.3.20 5001 > /dev/null 2>&1 &\'')
        os.system('ssh 2GB-rpi-4B \'cd new/containers/newWorker '
                  '&& docker-compose run --rm worker '
                  '192.168.3.14 5002 '
                  '192.168.3.20 5000 '
                  '192.168.3.20 5001 > /dev/null 2>&1 &\'')

    @staticmethod
    def stopRemoteWorkers():
        os.system('ssh 4GB-rpi-4B \''
                  'docker stop $(docker ps -a -q) '
                  '&& docker rm $(docker ps -a -q)\'')
        os.system('ssh 2GB-rpi-4B \''
                  'docker stop $(docker ps -a -q) '
                  '&& docker rm $(docker ps -a -q)\'')

    def run(self, schedulerName):
        self.removeLogs()

        config_ = {
            'cores': ['0', '1', '2', '3', '4-5', '6-7'],
            'cpuFrequencies': [10000, 15000, 20000, 25000, 10000, 20000],
            'memories': ['2g', '2g', '2g', '4g', '4g', '4g', '4g']
        }

        repeatTimes = 50
        sleepEachRound = 50
        respondTimes = [0 for _ in range(repeatTimes)]
        for i in range(repeatTimes):
            self.stopRemoteWorkers()
            self.stopAllContainers()
            self.runRemoteWorkers()
            logger = self.runRemoteLogger()
            master = self.runMaster(schedulerName)
            workers_ = self.runWorkers(config_)
            self.logger.debug('Sleep 20 seconds waiting for workers connect to master ...')
            sleep(20)
            user = self.runUser('User')
            self.logger.debug('Sleep %d seconds waiting for respondTime to be normal ...' % sleepEachRound)
            sleep(sleepEachRound)
            user.stop()
            respondTimes[i] = self.readRespondTime()
            self.logger.debug('[*] Result-[%d/%d]: %s', (i + 1), repeatTimes, str(respondTimes))
        self.saveRes(schedulerName, respondTimes)
        self.logger.info(respondTimes)

    @staticmethod
    def saveRes(schedulerName, respondTimes):
        with open(schedulerName + '.json', 'w+') as f:
            json.dump(respondTimes, f)
            f.close()


if __name__ == '__main__':
    experiment = Experiment()
    experiment.run('NSGA2')
    experiment.run('NSGA3')
    experiment.run('CTAEA')
    # Experiment().runUser('User')
