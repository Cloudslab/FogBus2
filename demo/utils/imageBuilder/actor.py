from .base import ImageBuilder


class ActorImageBuilder(ImageBuilder):

    def __init__(self):
        ImageBuilder.__init__(self, composeFilePath='actor')
