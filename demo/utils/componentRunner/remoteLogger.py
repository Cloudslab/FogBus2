from .base import BaseRunner


class RemoteLoggerRunner(BaseRunner):
    def __init__(self):
        BaseRunner.__init__(self, componentName='remoteLogger')
       