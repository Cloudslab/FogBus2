from logging import DEBUG

from ..tools import newDebugLogger


class DebugLogPrinter:
    def __init__(
            self,
            logLevel: int = DEBUG,
            loggerName: str = 'TempDebugLogger'):
        self.logLevel = logLevel
        self.debugLogger = newDebugLogger(
            loggerName=loggerName, levelName=self.logLevel)

    def renewDebugLogger(
            self,
            debugLoggerName,
            logLevel=None):
        if logLevel is None:
            logLevel = self.logLevel
        self.debugLogger = newDebugLogger(
            loggerName=debugLoggerName,
            levelName=logLevel)
