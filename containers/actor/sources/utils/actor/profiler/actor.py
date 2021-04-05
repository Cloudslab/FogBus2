from .images import ImagesProfiler


class ActorProfiler(ImagesProfiler):

    def profileAll(self):
        self.profileImages()
        self.profileRunningContainers()
        self.profileResources()
