from .base import ImageBuilder


class UserImageBuilder(ImageBuilder):

    def __init__(self):
        ImageBuilder.__init__(self, composeFilePath='user')
