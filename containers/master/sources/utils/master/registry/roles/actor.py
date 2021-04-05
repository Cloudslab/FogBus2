from ....types.basic.address import Address
from ....types.component import Component
from ....types.component.role import ComponentRole
from ....types.hostProfiles import ActorResources


class Actor(Component):

    def __init__(
            self,
            addr: Address = ('0.0.0.0', 0),
            hostID: str = None,
            componentID: str = None,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            actorResources: ActorResources = ActorResources()):
        Component.__init__(
            self,
            role=ComponentRole.ACTOR,
            addr=addr,
            hostID=hostID,
            componentID=componentID,
            name=name,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent)
        self.actorResources = actorResources
