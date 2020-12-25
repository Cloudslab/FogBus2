import cv2
from broker import Broker


# TODO: Generalise this
class ApplicationUserSide:

    def __init__(self, appID: int, appName: str, broker: Broker, videoPath=None):
        self.appID: int = appID
        self.broker: Broker = broker
        self.appName: str = appName
        self.capture = cv2.VideoCapture(0) if videoPath is None \
            else cv2.VideoCapture(videoPath)

    def run(self):
        self.broker.run()

        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            width = frame.shape[1]
            height = frame.shape[0]
            targetWidth = int(width * 640 / height)
            frame = cv2.resize(frame, (targetWidth, 640))
            resultFrame = self.broker.submit(self.appID, frame)
            while resultFrame is None:
                resultFrame = self.broker.submit(self.appID, frame)
            cv2.imshow("App-%d %s" % (self.appID, self.appName), resultFrame)
            if cv2.waitKey(1) == ord('q'):
                break
        self.capture.release()


if __name__ == '__main__':
    pass
