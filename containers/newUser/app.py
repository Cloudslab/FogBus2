import cv2
from broker import Broker


class ApplicationUserSide:

    def __init__(self, appID: int, broker: Broker):
        self.appID: int = appID
        self.broker: Broker = broker

    def run(self):
        self.broker.run()
        capture = cv2.VideoCapture(0)

        while True:
            ret, frame = capture.read()
            if not ret:
                break
            frame = self.broker.submit(self.appID, frame)
            cv2.imshow("App-1", frame)
            if cv2.waitKey(1) == ord('q'):
                break
        capture.release()


if __name__ == '__main__':
    pass
