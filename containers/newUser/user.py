import logging
import sys

from broker import Broker
from apps import FaceDetection, FaceAndEyeDetection, ColorTracking

if __name__ == "__main__":
    broker = Broker(
        serverHost='http://127.0.0.1',
        serverPort=5000,
        dataHost='127.0.0.1',
        portSending=5001,
        portReceiving=5002,
        logLevel=logging.DEBUG)
    appID = int(sys.argv[1])
    videoPath = sys.argv[2] if len(sys.argv) > 2 else None

    if appID == 0:
        app = FaceDetection(0, broker, videoPath)
        app.run()
    elif appID == 1:
        app = FaceAndEyeDetection(1, broker, videoPath)
        app.run()
    elif appID == 2:
        app = ColorTracking(2, broker, videoPath)
        app.run()
