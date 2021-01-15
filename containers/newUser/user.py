import logging
import sys

from datatype import Broker
from apps import FaceDetection, FaceAndEyeDetection, ColorTracking, VideoOCR

if __name__ == "__main__":

    appID = int(sys.argv[1])
    targetWidth = int(sys.argv[2])
    videoPath = sys.argv[3] if len(sys.argv) > 3 else None

    if appID == 1:
        broker = Broker(
            masterIP='127.0.0.1',
            masterPort=5000,
            remoteLoggerHost='127.0.0.1',
            remoteLoggerPort=5001,
            taskIDs=[1],
            logLevel=logging.DEBUG)
        app = FaceDetection(1, broker, videoPath, targetWidth=targetWidth)
        app.run()
    elif appID == 2:
        broker = Broker(
            masterIP='127.0.0.1',
            masterPort=5000,
            remoteLoggerHost='127.0.0.1',
            remoteLoggerPort=5001,
            taskIDs=[1, 2],
            logLevel=logging.DEBUG)
        app = FaceAndEyeDetection(2, broker, videoPath, targetWidth=targetWidth)
        app.run()
    elif appID == 3:

        broker = Broker(
            masterIP='127.0.0.1',
            masterPort=5000,
            remoteLoggerHost='127.0.0.1',
            remoteLoggerPort=5001,
            taskIDs=[3],
            logLevel=logging.DEBUG)
        app = ColorTracking(3, broker, videoPath, targetWidth=targetWidth)
        app.run()
    elif appID == 4:

        broker = Broker(
            masterIP='127.0.0.1',
            masterPort=5000,
            remoteLoggerHost='127.0.0.1',
            remoteLoggerPort=5001,
            taskIDs=[4, 5],
            logLevel=logging.DEBUG)
        app = VideoOCR(4, broker, videoPath, targetWidth=targetWidth)
        app.run()
