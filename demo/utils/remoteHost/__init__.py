import os


class RemoteHost:

    def __init__(self, user: str, host: str, port: int = 22):
        self.port = port
        self.host = host
        self.user = user
        self.ssh = 'ssh -p %d' % self.port + \
                   ' %s@%s' % (self.user, self.host)
        self.scriptPath = os.path.abspath(
            __file__[:-len(os.path.basename(__file__))])
        self.repoPath = os.path.join(
            self.scriptPath,
            '..%s..%s..%s' % (os.sep, os.sep, os.sep))
        self.remoteRepoPath = '~/fogbus2'

    def runCommand(self, remoteCommand: str, background: bool = False):
        command = '%s' % self.ssh + \
                  ' "%s"' % remoteCommand
        if background:
            command += ' &'
        return os.system(command=command)

    def uploadCode(self):
        codeTarPath = os.path.join(self.scriptPath, 'code.tar')
        command = 'cd %s' % self.repoPath + \
                  ' && git archive -o %s --format=tar HEAD' % codeTarPath
        if os.system(command=command) != 0:
            return
        command = 'scp -P %d' % self.port + \
                  ' %s "%s@%s:/tmp"' % (codeTarPath, self.user, self.host)
        if os.system(command=command) != 0:
            return
        command = 'rm %s' % codeTarPath
        if os.system(command=command) != 0:
            return
        command = 'mkdir -p %s' % self.remoteRepoPath + \
                  ' && tar xf /tmp/code.tar -C %s' % self.remoteRepoPath
        return self.runCommand(remoteCommand=command)

    def buildImages(self):
        command = 'python %s/demo/demo.py' % self.remoteRepoPath + \
                  ' --buildAll'
        return self.runCommand(remoteCommand=command)

    def runActor(self, hostIP: str = None):
        tempContainerName = 'TempActor'
        # command = 'docker container rm -f %s' % tempContainerName
        # self.runCommand(remoteCommand=command)
        command = 'cd %s/containers/actor' \
                  ' && docker-compose run' \
                  ' --rm' \
                  ' --name %s' \
                  ' fogbus2-actor' \
                  ' --bindIP %s' \
                  ' --containerName %s' % (
                      self.remoteRepoPath,
                      tempContainerName,
                      self.host,
                      tempContainerName)
        if hostIP is not None:
            command += ' --masterIP %s' % hostIP + \
                       ' --masterPort 5001' \
                       ' --remoteLoggerIP %s' % hostIP + \
                       ' --remoteLoggerPort 5000'
        self.runCommand(remoteCommand=command, background=True)


if __name__ == '__main__':
    remoteHost = RemoteHost(user='ubuntu', host='192.168.3.49')
    remoteHost.runActor()
