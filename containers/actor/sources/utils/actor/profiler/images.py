from docker import from_env as initDockerClient

from .resources import ResourcesProfiler
from ...component.basic import BasicComponent
from ...types.hostProfiles import ActorResources


class ImagesProfiler(ResourcesProfiler):

    def __init__(
            self,
            basicComponent: BasicComponent,
            resources: ActorResources = ActorResources(),
            dockerClient=initDockerClient()):
        ResourcesProfiler.__init__(
            self, basicComponent=basicComponent, resources=resources)
        self.dockerClient = dockerClient

    def profileImages(self):
        # self.basicComponent.debugLogger.info('Profiling images...')
        imageObjList = self.dockerClient.images.list()
        images = set()
        for image in imageObjList:
            tags = image.tags
            if not len(tags):
                continue
            images.update(tags)
        self.resources.images = images

    def profileRunningContainers(self):
        # self.basicComponent.debugLogger.info('Profiling RunningContainers...')
        containerList = self.dockerClient.containers.list()
        runningContainers = set()
        for container in containerList:
            containerName = container.name
            if not len(containerName):
                continue
            runningContainers.add(containerName)
        self.resources.runningContainers = runningContainers
