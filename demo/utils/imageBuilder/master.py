from .base import ImageBuilder


class MasterImageBuilder(ImageBuilder):

    def __init__(self):
        ImageBuilder.__init__(self, composeFilePath='master')
