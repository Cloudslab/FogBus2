import sys
import logging
from apps import *
from datatype import Broker

if __name__ == '__main__':
    apps = [TestApp(0), FaceDetection(1), EyeDetection(2), ColorTracking(3)]
    app = None
    userID = None
    appID = None
    token = None
    nextWorkerToken = None
    if len(sys.argv) > 3:
        userID = int(sys.argv[1])
        appID = int(sys.argv[2])
        token = sys.argv[3]
        nextWorkerToken = sys.argv[4]
        app = apps[appID]

    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        thisIP='127.0.0.1',
        app=app,
        userID=userID,
        appID=appID,
        token=token,
        nextWorkerToken=nextWorkerToken,
        logLevel=logging.DEBUG)
    broker.run()
