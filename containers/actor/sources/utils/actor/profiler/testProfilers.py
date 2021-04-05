import unittest

from .actor import ActorProfiler
from ...types import HostProfiles


class MyTestCase(unittest.TestCase):
    resources = HostProfiles()
    actorProfiler = ActorProfiler(resources=resources)

    def testProfileResources(self):
        self.actorProfiler.profileResources()
        print('cpu', self.actorProfiler.resources.cpu)
        print('memory', self.actorProfiler.resources.memory)
        self.assertTrue(True)

    def testProfileImages(self):
        self.actorProfiler.profileImages()
        print('images', self.actorProfiler.images)
        self.assertTrue(True)

    def testProfileRunningContainers(self):
        self.actorProfiler.profileRunningContainers()
        print('runningContainers', self.actorProfiler.runningContainers)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
