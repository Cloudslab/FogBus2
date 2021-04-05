from .base import ImageBuilder


class RemoteLoggerImageBuilder(ImageBuilder):

    def __init__(self):
        ImageBuilder.__init__(self, composeFilePath='remoteLogger')
