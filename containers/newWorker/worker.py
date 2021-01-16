import sys
import logging
from apps import *
from datatype import Broker

if __name__ == '__main__':
    app = None
    userID = None
    taskName = None
    token = None
    childTaskTokens = None
    ownedBy = None
    userName = None
    if len(sys.argv) > 4:
        userID = int(sys.argv[1])
        taskName = sys.argv[2]
        token = sys.argv[3]
        childTaskTokens = sys.argv[4]
    if len(sys.argv) > 6:
        ownedBy = int(sys.argv[5])
        userName = sys.argv[6]

    print('userID, taskName, token, childTaskTokens, ownedBy, userName')
    print(userID, taskName, token, childTaskTokens, ownedBy, userName)
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
        masterIP='127.0.0.1',
        masterPort=5000,
        remoteLoggerHost='127.0.0.1',
        remoteLoggerPort=5001,
        thisIP='127.0.0.1',
        task=app,
        userID=userID,
        taskName=taskName,
        token=token,
        childTaskTokens=childTaskTokens,
        ownedBy=ownedBy,
        userName=userName,
        logLevel=logging.DEBUG)
    broker.run()
