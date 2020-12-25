import logging
import sys

from broker import Broker
from app import ApplicationUserSide

if __name__ == "__main__":
    broker = Broker(
        serverHost='http://127.0.0.1',
        serverPort=5000,
        dataHost='127.0.0.1',
        portSending=5001,
        portReceiving=5002,
        logLevel=logging.DEBUG)
    appID = int(sys.argv[1])
    appName = sys.argv[2]
    app = ApplicationUserSide(appID, appName, broker)
    app.run()
