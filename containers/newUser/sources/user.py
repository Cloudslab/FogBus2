import logging
import sys

from datatype import Broker
from apps import FaceDetection, FaceAndEyeDetection, ColorTracking, VideoOCR

if __name__ == "__main__":

    appIDOrName = sys.argv[1]
    targetWidth = int(sys.argv[2])
    videoPath = sys.argv[3] if len(sys.argv) > 3 else None
    broker = Broker(
        masterIP='127.0.0.1',
        masterPort=5000,
        remoteLoggerHost='127.0.0.1',
        remoteLoggerPort=5001,
        appName=appIDOrName,
        logLevel=logging.DEBUG)
    app = None
    if appIDOrName == 'FaceDetection':
        app = FaceDetection(1, broker, videoPath, targetWidth=targetWidth)
    elif appIDOrName == 'FaceAndEyeDetection':
        app = FaceAndEyeDetection(2, broker, videoPath, targetWidth=targetWidth)
    elif appIDOrName == 'ColorTracking':
        app = ColorTracking(3, broker, videoPath, targetWidth=targetWidth)
    elif appIDOrName == 'VideoOCR':
        app = VideoOCR(4, broker, videoPath, targetWidth=targetWidth)
    if app is not None:
        app.run()
