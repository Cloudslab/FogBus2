import os

from .camelToSnake import camelToSnake


class TaskExecutorImageBuilder:

    def __init__(self):
        containersAbsPath = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        self.dockerFilesFolder = os.path.join(
            containersAbsPath,
            '..%s..%s..%scontainers' % (os.sep, os.sep, os.sep),
            'taskExecutor%sdockerFiles' % os.sep)

    def build(
            self,
            proxy: str = '',
            platforms: str = '',
            dockerHubUsername: str = '',
            push: bool = False) -> int:

        for folder in os.listdir(self.dockerFilesFolder):
            folderAbsPath = os.path.join(self.dockerFilesFolder, folder)
            composeFilepath = os.path.join(folderAbsPath, 'docker-compose.yml')
            if not os.path.exists(composeFilepath):
                continue
            # copy sources folder
            os.system('cp -r %s/../../sources %s/sources' % (
                folderAbsPath, folderAbsPath))
            ret = -1
            if platforms != '':
                ret = self.crossCompile(
                    composeFolder=folderAbsPath,
                    proxy=proxy,
                    platforms=platforms,
                    dockerHubUsername=dockerHubUsername,
                    push=push)
            else:
                command = 'cd %s && docker-compose build' % folderAbsPath
                
                if proxy != '':
                    command += ' --build-arg http_proxy=%s' % proxy + \
                            ' --build-arg https_proxy=%s' % proxy
                ret = os.system(
                    'cd %s && docker-compose build' % folderAbsPath)
            # delete sources folder
            os.system('rm -rf %s/sources' % folderAbsPath)

            if ret != 0:
                raise Exception('Failed to build: %s' % composeFilepath)
        return 0

    @staticmethod
    def crossCompile(
            composeFolder: str,
            proxy: str = '',
            platforms: str = 'linux/amd64,'
                             'linux/arm64,'
                             'linux/arm/v7,'
                             'linux/arm/v6',
            dockerHubUsername: str = '',
            push: bool = False):
        basename = os.path.basename(composeFolder)
        command = 'cd %s ' % composeFolder + \
                  ' && docker buildx build ' + \
                  ' --platform %s ' % platforms
        if proxy != '':
            command += ' --build-arg http_proxy=%s' % proxy + \
                       ' --build-arg https_proxy=%s' % proxy
        basename = camelToSnake(basename)
        if len(dockerHubUsername):
            command += ' -t %s/fogbus2-%s' % (dockerHubUsername,
                                              basename)
        if push:
            command += ' --push'
        command += ' .'
        print(command)
        ret = os.system(command)
        if ret != 0:
            raise Exception('Failed to build: %s' % command)
        return ret


if __name__ == '__main__':
    builder = TaskExecutorImageBuilder()
    builder.build()
