import logging
from apps import *
from datatype import Broker

if __name__ == '__main__':
    apps = [TestApp(0), FaceDetection(1), EyeDetection(2), ColorTracking(3)]
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        thisIP='127.0.0.1',
        thisPort=6000,
        appIDs=apps,
        logLevel=logging.DEBUG)
    broker.run()
