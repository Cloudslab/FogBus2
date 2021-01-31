import logging
import threading
import docker
import os
from logger import get_logger
from tqdm import tqdm
from typing import List


class Experiment:

    def __init__(self):
        self.currPath = os.path.abspath(os.path.curdir)
        self.client = docker.from_env()
        self.logger = get_logger('Experiment', level_name=logging.DEBUG)

    def stopAllContainers(self):
        containerList = self.client.containers.list()
        events: List[threading.Event] = [threading.Event() for _ in range(len(containerList))]
        for i, container in enumerate(containerList):
            self.stopContainer(container, events[i])
        for event in tqdm(
                events,
                desc='Stopping Running Containers',
                unit='containers'):
            event.wait()

    def stopContainer(self, container, event):
        threading.Thread(
            target=self.__stopContainer,
            args=(container, event)).start()

    def __stopContainer(self, container, event):
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
            **kwargs)

    def runRemoteLogger(self):
        return self._run(
            name='RemoteLogger',
            auto_remove=True,
            image='remote-logger',
            network_mode='host',
            volumes={
                '%s/newLogger/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'}
            },
            working_dir='/workplace',
            command='192.168.3.20 5001 '
                    '192.168.3.20 5000 '
                    '192.168.3.20 5001')

    def runMaster(self):
        return self._run(
            name='Master',
            auto_remove=True,
            image='master',
            network_mode='host',
            volumes={
                '%s/newMaster/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'}
            },
            working_dir='/workplace',
            command='192.168.3.20 5000 '
                    '192.168.3.20 5000 '
                    '192.168.3.20 5001')

    def runWorker(self, core: str, cpuFreq: int, mem: str, name: str):
        return self._run(
            name=name,
            auto_remove=True,
            image='worker',
            cpuset_cpus=core,
            cpu_period=cpuFreq,
            mem_limit=mem,
            network_mode='host',
            volumes={
                '%s/newWorker/sources' % self.currPath: {
                    'bind': '/workplace',
                    'mode': 'rw'},

                '/var/run/docker.sock': {
                    'bind': '/var/run/docker.sock',
                    'mode': 'rw'}
            },
            working_dir='/workplace',
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


if __name__ == '__main__':
    experiment = Experiment()
    experiment.stopAllContainers()
    logger = experiment.runRemoteLogger()
    master = experiment.runMaster()
    config_ = {
        'cores': ['0', '1', '2', '3', '4-5', '6-7'],
        'cpuFrequencies': [10000, 15000, 20000, 25000, 10000, 20000],
        'memories': ['2g', '2g', '2g', '4g', '4g', '4g', '4g']
    }
    workers_ = experiment.runWorkers(config_)
