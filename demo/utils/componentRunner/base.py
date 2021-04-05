import os


class BaseRunner:

    def __init__(self, componentName: str):
        currAbsPath = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        containerAbsDir = os.path.join(
            currAbsPath,
            '..%s..%s..%scontainers' % (os.sep, os.sep, os.sep))
        self.componentName = componentName
        self.componentFolder = os.path.join(
            containerAbsDir,
            componentName)

    def run(
            self,
            args: str,
            componentName: str = None,
            background: bool = True):
        if componentName is None:
            componentName = self.componentName
        tempContainerName = 'Temp%s' % componentName
        # os.system('docker container rm -f %s' % tempContainerName)
        command = 'cd %s' \
                  ' && docker-compose run' \
                  ' --rm' \
                  ' --name %s' \
                  ' %s' \
                  ' %s' \
                  ' --containerName %s' % (
                      self.componentFolder,
                      tempContainerName,
                      self.nameToImageName(componentName),
                      args,
                      tempContainerName)
        if background:
            command += ' &'
        os.system(command=command)

    @staticmethod
    def nameToImageName(componentName: str):
        if componentName in {'master', 'actor', 'user'}:
            return 'fogbus2-%s' % componentName

        if componentName == 'remoteLogger':
            return 'fogbus2-remote_logger'
        if componentName == 'taskExecutor':
            return 'fogbus2-task-executor'
        raise Exception('Component not supported: %s' % componentName)


if __name__ == '__main__':
    runner = BaseRunner('remoteLogger')
    runner.run(args='--bindIP 127.0.0.1')
