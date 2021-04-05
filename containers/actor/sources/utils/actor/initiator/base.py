from docker.client import DockerClient

from ...component.basic import BasicComponent


class BaseInitiator:

    def __init__(
            self,
            basicComponent: BasicComponent,
            isContainerMode: bool,
            dockerClient: DockerClient = None):
        self.basicComponent = basicComponent
        if dockerClient is not None:
            isContainerMode = True
        if not isContainerMode:
            return
        self.dockerClient = dockerClient
        self.me = self.basicComponent.me
