import logging
import sys

from broker import Broker
from apps import FaceDetection, FaceAndEyeDetection, ColorTracking

if __name__ == "__main__":

    broker = Broker(
        host='127.0.0.1',
        port=5000,
        logLevel=logging.DEBUG)
    appID = int(sys.argv[1])
    videoPath = sys.argv[2] if len(sys.argv) > 2 else None

    if appID == 0:
        app = FaceDetection(1, broker, videoPath)
        app.run()
    elif appID == 1:
        app = FaceAndEyeDetection(2, broker, videoPath)
        app.run()
    elif appID == 2:
        app = ColorTracking(3, broker, videoPath)
        app.run()
