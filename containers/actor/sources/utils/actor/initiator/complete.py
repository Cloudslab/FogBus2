from docker.client import DockerClient

from .actor import ActorInitiator
from .master import MasterInitiator
from .taskExecutor import TaskExecutorInitiator
from ...component.basic import BasicComponent
from ...types import CPU


class Initiator(TaskExecutorInitiator, ActorInitiator, MasterInitiator):

    def __init__(
            self,
            basicComponent: BasicComponent,
            isContainerMode: bool,
            dockerClient: DockerClient,
            cpu: CPU):
        self.basicComponent = basicComponent
        self.dockerClient = dockerClient
        TaskExecutorInitiator.__init__(
            self,
            basicComponent=basicComponent,
            isContainerMode=isContainerMode,
            dockerClient=dockerClient,
            cpu=cpu)
        ActorInitiator.__init__(
            self,
            basicComponent=basicComponent,
            isContainerMode=isContainerMode,
            dockerClient=dockerClient)
        MasterInitiator.__init__(
            self,
            basicComponent=basicComponent,
            isContainerMode=isContainerMode,
            dockerClient=dockerClient)
