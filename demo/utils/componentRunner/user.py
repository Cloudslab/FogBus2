import os


class UserRunner:

    def __init__(self):
        currAbsPath = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        containerAbsDir = os.path.join(
            currAbsPath,
            '..%s..%s..%scontainers' % (os.sep, os.sep, os.sep))

        self.componentName = 'user'
        self.componentFolder = os.path.join(
            containerAbsDir,
            self.componentName,
            'sources')

    def run(self, args: str):
        command = 'cd %s && python3.9 user.py %s' % (self.componentFolder, args)
        os.system(command=command)


if __name__ == '__main__':
    runner = UserRunner()
    runner.run('--bindIP 127.0.0.1')
