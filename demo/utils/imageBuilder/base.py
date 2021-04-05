import os

from .camelToSnake import camelToSnake


class ImageBuilder:

    def __init__(self, composeFilePath: str):
        currAbsPath = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        self.composeFilePath = os.path.join(
            currAbsPath,
            '..%s..%s..%scontainers' % (os.sep, os.sep, os.sep),
            composeFilePath,
            'docker-compose.yml')
        if not os.path.exists(self.composeFilePath):
            raise Exception('Not exist: %s' % self.composeFilePath)
        self.composeFolder = os.path.dirname(self.composeFilePath)

    def build(
            self,
            composeFolder: str = None,
            proxy: str = None,
            platforms: str = '',
            dockerHubUsername: str = '',
            push: bool = False) -> int:

        if composeFolder is None:
            composeFolder = self.composeFolder

        if proxy is None:
            if platforms:
                return self.crossCompile(
                    composeFolder=composeFolder,
                    platforms=platforms,
                    dockerHubUsername=dockerHubUsername,
                    push=push)
            return os.system('cd %s && docker-compose build' % composeFolder)

        ret = os.system('cd %s && docker-compose build'
                        ' --build-arg  HTTP_PROXY="%s"'
                        '  --build-arg  HTTPS_PROXY="%s"' % (
                            composeFolder, proxy, proxy))
        if ret != 0:
            raise Exception('Failed to build: %s' % composeFolder)
        return ret

    def crossCompile(
            self,
            composeFolder: str,
            platforms: str = 'linux/amd64,'
                             'linux/arm64,'
                             'linux/arm/v7,'
                             'linux/arm/v6',
            dockerHubUsername: str = '',
            push: bool = False):
        if composeFolder is None:
            composeFolder = self.composeFolder
        basename = os.path.basename(composeFolder)
        command = 'cd %s ' % composeFolder + \
                  ' && docker buildx build ' + \
                  ' --platform %s ' % platforms
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
    builder = ImageBuilder(composeFilePath='actor')
    builder.build()
