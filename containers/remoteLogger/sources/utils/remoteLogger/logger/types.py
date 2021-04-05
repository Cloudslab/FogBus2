from typing import Dict

from ...types.hostProfiles.images import Images
from ...types.hostProfiles.processingTime import ProcessingTime
from ...types.hostProfiles.actorResources import ActorResources
from ...types.hostProfiles.runningContainres import RunningContainers

AllImages = Dict[str, Images]
AllResources = Dict[str, ActorResources]
AllRunningContainers = Dict[str, RunningContainers]
AllDataRate = Dict[str, Dict[str, float]]
AllDelay = Dict[str, Dict[str, float]]
AllLatency = Dict[str, Dict[str, float]]
AllPacketSize = Dict[str, Dict[str, int]]
AllProcessingTime = Dict[str, ProcessingTime]
AllResponseTime = Dict[str, float]
