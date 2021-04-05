from ..logger import LoggerManager
from ...connection import HandlerReturn
from ...connection import MessageReceived


class LogHandler:

    def __init__(self, loggerManager: LoggerManager):
        self.loggerManager = loggerManager

    def handleProfiles(self, message: MessageReceived) -> HandlerReturn:
        profiles = message.data['profiles']
        imagesToMerge = {message.source.nameConsistent: profiles}
        self.loggerManager.mergeImages(imagesToMerge)
        return
