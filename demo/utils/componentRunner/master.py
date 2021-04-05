from .base import BaseRunner


class MasterRunner(BaseRunner):
    def __init__(self):
        BaseRunner.__init__(self, componentName='master')
