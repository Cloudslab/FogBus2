from abc import ABC
from collections import defaultdict
from threading import Event
from threading import Lock
from typing import DefaultDict
from typing import Dict
from typing import Tuple

from ..connection import BasicMessageHandler
from ..types import Address
from ..types import Component
from ..types import ComponentRole


class Communicator(BasicMessageHandler, ABC):
    locks: DefaultDict[str, Lock] = defaultdict(lambda: Lock())
    networkTimeDiff: Dict[Tuple[str, int], float] = {}
    isRegistered: Event = Event()

    def __init__(
            self,
            role: ComponentRole,
            addr: Address,
            portRange: Tuple[int, int],
            logLevel: int,
            masterAddr: Address,
            remoteLoggerAddr: Address,
            ignoreSocketError: bool = False):
        BasicMessageHandler.__init__(
            self,
            role=role,
            addr=addr,
            logLevel=logLevel,
            ignoreSocketError=ignoreSocketError,
            portRange=portRange)
        self.serveEvent.wait()
        self.me = Component(
            hostID=self.hostID,
            role=self.role,
            addr=self.addr)
        self.master = Component(
            role=ComponentRole.MASTER,
            addr=masterAddr)
        self.remoteLogger = Component(
            role=ComponentRole.REMOTE_LOGGER,
            addr=remoteLoggerAddr)

    def setName(
            self,
            addr,
            name: str = None,
            nameLogPrinting: str = None,
            nameConsistent: str = None,
            componentID: str = None,
            hostID: str = None,
            setIsRegistered: bool = False):

        self.setIdentities(
            addr=addr,
            name=name,
            componentID=componentID,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            hostID=hostID)
        self.me.setIdentities(
            addr=addr,
            name=name,
            componentID=componentID,
            nameLogPrinting=nameLogPrinting,
            nameConsistent=nameConsistent,
            hostID=hostID)
        self.renewDebugLogger(
            debugLoggerName=self.nameLogPrinting,
            logLevel=self.logLevel)
        if self.role in {ComponentRole.MASTER, ComponentRole.REMOTE_LOGGER}:
            self.isRegistered.set()
            return
        if setIsRegistered:
            self.isRegistered.set()
            return
