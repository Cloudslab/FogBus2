import sys
import logging
from apps import *
from datatype import Broker

if __name__ == '__main__':
    thisHost = sys.argv[1]
    masterHost = sys.argv[2]
    masterPort = int(sys.argv[3])
    remoteLoggerHost = sys.argv[4]
    remoteLoggerPort = int(sys.argv[5])
    app = None
    userID = None
    taskName = None
    token = None
    childTaskTokens = None
    ownedBy = None
    userName = None
    if len(sys.argv) > 9:
        userID = int(sys.argv[6])
        taskName = sys.argv[7]
        token = sys.argv[8]
        childTaskTokens = sys.argv[9]
    if len(sys.argv) > 11:
        ownedBy = int(sys.argv[10])
        userName = sys.argv[11]

    if taskName == 0:
        app = TestApp(0)
    elif taskName == 'FaceDetection':
        app = FaceDetection()
    elif taskName == 'EyeDetection':
        app = EyeDetection()
    elif taskName == 'ColorTracking':
        app = ColorTracking()
    elif taskName == 'BlurAndPHash':
        app = BlurAndPHash()
    elif taskName == 'OCR':
        app = OCR()

    if childTaskTokens == 'None':
        childTaskTokens = None
    if childTaskTokens is not None:
        childTaskTokens = childTaskTokens.split(',')
    broker = Broker(
        masterIP=masterHost,
        masterPort=masterPort,
        remoteLoggerHost=remoteLoggerHost,
        remoteLoggerPort=remoteLoggerPort,
        thisIP=thisHost,
        task=app,
        userID=userID,
        taskName=taskName,
        token=token,
        childTaskTokens=childTaskTokens,
        ownedBy=ownedBy,
        userName=userName,
        logLevel=logging.DEBUG)
    broker.run()
