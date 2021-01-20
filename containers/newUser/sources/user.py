import logging
import sys

from datatype import Broker
from apps import FaceDetection, FaceAndEyeDetection, ColorTracking, VideoOCR

if __name__ == "__main__":
    remoteLoggerHost = sys.argv[1]
    masterPort = int(sys.argv[2])
    appIDOrName = sys.argv[3]
    targetWidth = int(sys.argv[4])
    videoPath = sys.argv[5] if len(sys.argv) > 5 else None
    broker = Broker(
        masterIP=remoteLoggerHost,
        masterPort=masterPort,
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
