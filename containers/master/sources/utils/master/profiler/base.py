from .dataRate import DataRateProfiler
from .resources import ResourcesProfiler
from ..logger import LoggerManager
from ..registry.roles import Actor
from ...component import BasicComponent


class MasterProfiler(DataRateProfiler):

    def __init__(
            self,
            basicComponent: BasicComponent,
            loggerManager: LoggerManager,
            minActors: int):
        DataRateProfiler.__init__(
            self,
            basicComponent=basicComponent,
            loggerManager=loggerManager,
            minActors=minActors)
        self.me = ResourcesProfiler(
            basicComponent=basicComponent)

    def updateActorResources(self, actor: Actor):
        nameConsistent = actor.nameConsistent
        imagesToMerge = {nameConsistent: actor.actorResources.images}
        self.loggerManager.mergeImages(imagesToMerge=imagesToMerge)
        toMerge = {nameConsistent: actor.actorResources.runningContainers}
        self.loggerManager.mergeRunningContainers(toMerge)
        actorResourcesToMerge = {nameConsistent: actor.actorResources}
        self.loggerManager.mergeResources(actorResourcesToMerge)
