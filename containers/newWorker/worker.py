import sys
import logging
from apps import *
from datatype import Broker

if __name__ == '__main__':
    app = None
    userID = None
    appID = None
    token = None
    nextWorkerToken = None
    ownedBy = None
    userName = None
    if len(sys.argv) > 4:
        userID = int(sys.argv[1])
        appID = int(sys.argv[2])
        token = sys.argv[3]
        nextWorkerToken = sys.argv[4]
    if len(sys.argv) > 6:
        ownedBy = int(sys.argv[5])
        userName = sys.argv[6]

    if appID == 0:
        app = TestApp(0)
    elif appID == 1:
        app = FaceDetection()
    elif appID == 2:
        app = EyeDetection()
    elif appID == 3:
        app = ColorTracking()
    elif appID == 4:
        app = BlurAndPHash()
    elif appID == 5:
        app = OCR()

    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        remoteLoggerHost='127.0.0.1',
        remoteLoggerPort=5001,
        thisIP='127.0.0.1',
        task=app,
        userID=userID,
        appID=appID,
        token=token,
        nextWorkerToken=nextWorkerToken,
        ownedBy=ownedBy,
        userName =userName,
        logLevel=logging.DEBUG)
    broker.run()
