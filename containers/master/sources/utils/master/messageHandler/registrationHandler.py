from ..profiler.base import MasterProfiler
from ..registry.base import Registry
from ...component import BasicComponent
from ...connection import MessageReceived
from ...types.component.role import ComponentRole


class RegistrationHandler:

    def __init__(
            self,
            basicComponent: BasicComponent,
            registry: Registry,
            profiler: MasterProfiler):
        self.basicComponent = basicComponent
        self.profiler = profiler
        self.registry = registry
        self.debugLogger = self.basicComponent.debugLogger

    def handleRegister(self, message: MessageReceived):
        source = message.source
        if source.role is ComponentRole.USER:
            pass
            # self.profiler.dataRateTestEvent.wait()
        return self.registry.registerClient(message=message)
