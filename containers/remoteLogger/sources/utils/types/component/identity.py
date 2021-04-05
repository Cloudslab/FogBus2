from .role import ComponentRole
from ..basic import Address


class ComponentIdentity:
    def __init__(
            self,
            addr: Address,
            role: ComponentRole = ComponentRole.DEFAULT,
            hostID: str = None,
            componentID: str = None,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None):
        self.role = role
        self.addr = addr
        if componentID is None:
            self.componentID = '?'
        else:
            self.componentID = componentID
        if hostID is None:
            self.hostID = self.generateHostID()
        else:
            self.hostID = hostID
        if name is None:
            self.name = '%s-%s_%s-%d' % (
                self.role.value, self.componentID, addr[0], addr[1])
        else:
            self.name = name
        if nameLogPrinting is None:
            self.nameLogPrinting = self.name
        else:
            self.nameLogPrinting = nameLogPrinting
        if nameConsistent is None:
            self.nameConsistent = '%s_%s' % (self.role.value, self.hostID)
        else:
            self.nameConsistent = nameConsistent

    def generateHostID(self):
        info = self.addr[0]
        # return sha256(info.encode('utf-8')).hexdigest()
        return info

    @staticmethod
    def getHostIDFromNameConsistent(nameConsistent: str):
        return nameConsistent[-64:]

    def setIdentities(
            self,
            addr: Address = None,
            name: str = None,
            componentID: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            hostID: str = None):
        if addr is not None:
            self.addr = addr
        if name is not None:
            self.name = name
        else:
            self.name = '%s-%s_%s-%d' % (
                self.role.value, self.componentID, self.addr[0], self.addr[1])
        if componentID is not None:
            self.componentID = componentID
        if nameLogPrinting is not None:
            self.nameLogPrinting = nameLogPrinting
        else:
            self.nameLogPrinting = self.name
        if nameConsistent is not None:
            self.nameConsistent = nameConsistent
        if hostID is not None:
            self.hostID = hostID
