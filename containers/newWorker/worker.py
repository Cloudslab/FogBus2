import logging
from apps import appList
from broker import Broker

if __name__ == '__main__':
    broker = Broker(
        serverHost='http://127.0.0.1',
        serverPort=5000,
        dataHost='127.0.0.1',
        portSending=5001,
        portReceiving=5002,
        appList=appList,
        logLevel=logging.DEBUG)
    broker.run()
