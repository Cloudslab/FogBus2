from .base import BaseRunner


class ActorRunner(BaseRunner):
    def __init__(self):
        BaseRunner.__init__(self, componentName='actor')
