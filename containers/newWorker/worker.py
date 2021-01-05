import logging
from apps import *
from broker import Broker

if __name__ == '__main__':
    apps = [TestApp(0), FaceDetection(1), EyeDetection(2), ColorTracking(3)]
    broker = Broker(
        host='127.0.0.1',
        port=5000,
        appIDs=apps,
        logLevel=logging.DEBUG)
    broker.run()
