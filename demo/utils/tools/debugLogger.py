from logging import DEBUG
from logging import FileHandler
from logging import Formatter
from logging import getLogger
from logging import StreamHandler


# https://www.programcreek.com/python/example/192/logging.Formatter
# https://stackoverflow.com/questions/533048
def newDebugLogger(
        loggerName='TemporaryDebugLogger',
        levelName=DEBUG,
        createFile=False):
    """
    create a new logger
    :param loggerName: string, logs logger name
    :param levelName: string, log printing level
    :param createFile: bool, whether log in to a file
    :return: a logger
    """
    logfileName = loggerName + '.log'
    # create logger for prd_ci
    log = getLogger(loggerName)
    log.setLevel(levelName)
    # create formatter and add it to the handlers
    formatter = Formatter(
        fmt='[%(asctime)s,%(msecs)d][%(pathname)s:%(lineno)d][%(name)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    if createFile:
        # create file handler for logger.
        fh = FileHandler(logfileName)
        fh.setLevel(level=levelName)
        fh.setFormatter(formatter)
        # add handlers to logger.
        log.addHandler(fh)
    # create console handler for logger.
    ch = StreamHandler()
    ch.setLevel(level=levelName)
    ch.setFormatter(formatter)
    # while log.handlers:
    #     log.handlers.pop()
    log.addHandler(ch)
    return log
