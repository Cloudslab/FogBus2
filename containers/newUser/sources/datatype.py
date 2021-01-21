import cv2

from abc import abstractmethod
from queue import Queue
from systemInfo import SystemInfo


class NodeSpecs:
    def __init__(
            self,
            cores,
            ram,
            disk,
            network):
        self.cores = cores
        self.ram = ram
        self.disk = disk
        self.network = network

    def info(self):
        return "\
                Cores: %d\n\
                ram: %d GB\n\
                disk: %d GB\n\
                network: %d Mbps\n" % (self.cores, self.ram, self.disk, self.cores)


class UserSysInfo(SystemInfo):
    pass


class ApplicationUserSide:

    def __init__(
            self,
            videoPath=None,
            targetWidth: int = 640):
        self.appName = None
        self.capture = cv2.VideoCapture(0) if videoPath is None \
            else cv2.VideoCapture(videoPath)
        self.result: Queue = Queue()
        self.dataToSubmit: Queue = Queue()
        self.targetWidth = targetWidth

    def resizeFrame(self, frame):
        width = frame.shape[1]
        height = frame.shape[0]
        resizedWidth = int(width * self.targetWidth / height)
        return cv2.resize(frame, (resizedWidth, self.targetWidth))

    @abstractmethod
    def run(self):
        pass


if __name__ == '__main__':
    pass
