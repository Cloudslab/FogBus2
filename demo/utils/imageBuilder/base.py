import os

from .camelToSnake import camelToSnake


def crossCompileBase(
        composeFolder: str,
        proxy: str = None,
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
    if proxy is not None:
        command += ' --build-arg http_proxy=%s' % proxy + \
                   ' --build-arg https_proxy=%s' % proxy
    basename = camelToSnake(basename)
    if len(dockerHubUsername):
        command += ' -t %s/fogbus2-%s' % (dockerHubUsername,
                                          basename)
    if push:
        command += ' --push'
    command += ' .'
    print('[*] ' + command)
    ret = os.system(command)
    if ret != 0:
        raise Exception('Failed to build: %s' % command)
    return ret

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

        if platforms:
            return self.crossCompile(
                composeFolder=composeFolder,
                proxy=proxy,
                platforms=platforms,
                dockerHubUsername=dockerHubUsername,
                push=push)
        command = 'cd %s && docker-compose build' % composeFolder
        if proxy is not None:
            command += ' --build-arg http_proxy=%s' % proxy + \
                       ' --build-arg https_proxy=%s' % proxy
        return os.system(command)

    def crossCompile(
            self,
            composeFolder: str,
            proxy: str = None,
            platforms: str = 'linux/amd64,'
                             'linux/arm64,'
                             'linux/arm/v7,'
                             'linux/arm/v6',
            dockerHubUsername: str = '',
            push: bool = False):
        if composeFolder is None:
            composeFolder = self.composeFolder
        return crossCompileBase(
            composeFolder=composeFolder,
            proxy=proxy,
            platforms=platforms,
            dockerHubUsername=dockerHubUsername,
            push=push)


if __name__ == '__main__':
    builder = ImageBuilder(composeFilePath='actor')
    builder.build()
