import os
import sys
import cv2
import numpy as np
import pytesseract
import editdistance
from time import time


def get_pHash(img):
    hashLen = 32

    imgGray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                         (hashLen, hashLen),
                         cv2.INTER_AREA)
    hight, width = imgGray.shape[:2]
    matrixOriginal = np.zeros((hight, width), np.float32)
    matrixOriginal[:hight, :width] = imgGray

    matrix = cv2.dct(cv2.dct(matrixOriginal))
    matrix.resize(hashLen, hashLen)
    matrixFlatten = matrix.flatten()

    averageValue = sum(matrixFlatten) * 1. / len(matrixFlatten)
    pHash = 0
    for i in matrixFlatten:
        pHash <<= 1
        if i >= averageValue:
            pHash += 1
    return pHash


def get_ham_distance(x, y):
    tmp = x ^ y
    distance = 0

    while tmp > 0:
        distance += tmp & 1
        tmp >>= 1

    return distance


def get_dff(imgA, imgB):
    return get_ham_distance(get_pHash(imgA), get_pHash(imgB))


def resize(img):
    factor = 1080/img.shape[1]
    return cv2.resize(img, (1080, round(img.shape[0] * factor)))


def showWindow(frame, preFrame):
    frame = np.hstack((frame, preFrame))
    cv2.imshow('VIDEO', frame)
    cv2.waitKey(1)


def saveFrame(frame, frameNumber, text):
    cv2.imwrite("./output/%d.jpg" % frameNumber, frame)
    f = open("./output/%d.txt" % frameNumber, "w")
    f.write(text)
    f.close()


def run():
    thresholdLaplacian = 120
    thresholdDiffStop = 120
    thresholdDiffPre = 25
    thresholdEditDistance = 800

    vcap = cv2.VideoCapture(sys.argv[1])
    preStopFrame = None
    preFrame = None
    preText = None
    flag = True
    n = 0
    frameNumber = 0
    totalFrame = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
    gotFrame = 0

    while(1):
        ret, frame = vcap.read()
        if ret:
            print("[*] Processing %s: %d/%d ,got %d frames." %
                    (sys.argv[1], frameNumber, totalFrame, gotFrame), end='\r')
            frameNumber += 1
            frame = resize(frame)
            preFrame = frame
            # blur metric
            laplacian = cv2.Laplacian(frame, cv2.CV_64F).var()
            if laplacian > thresholdLaplacian:
                preStopFrame = frame
                preStopPHash = get_pHash(preStopFrame)
                showWindow(frame, frame)
                saveFrame(frame, frameNumber,
                          pytesseract.image_to_string(frame))
                gotFrame += 1
                break
        else:
            break

    if preFrame is None or preStopFrame is None:
        return

    prePHash = get_pHash(preFrame)
    while(1):
        ret, frame = vcap.read()
        if ret:
            print("[*] Processing %s: %d/%d, got %d frames." %
                  (sys.argv[1], frameNumber, totalFrame, gotFrame), end='\r')
            frameNumber += 1
            frame = resize(frame)
            # blur metric
            laplacian = cv2.Laplacian(frame, cv2.CV_64F).var()

            currPHash = get_pHash(frame)
            diffStop = get_ham_distance(preStopPHash, currPHash)
            diffPre = get_ham_distance(prePHash, currPHash)

            prePHash = currPHash

            # print(diffStop, diffPre, laplacian)

            if diffStop < thresholdDiffStop \
                    and diffPre > thresholdDiffPre \
                    and laplacian > thresholdLaplacian:
                n += 1
                if n > 3:

                    n = 0
                    text = pytesseract.image_to_string(frame)

                    if preText is not None:
                        editDistance = editdistance.eval(preText, text)
                        if editDistance > thresholdEditDistance:
                            preStopFrame = frame
                            preStopPHash = currPHash
                            saveFrame(frame, frameNumber, text)
                            gotFrame += 1
                    preText = text
            showWindow(preStopFrame, preFrame)
            preFrame = frame
        else:
            break
    
    print("\r\n[*] Done, got %d frames. See ./output" % gotFrame)


if __name__ == '__main__':
    if not os.path.exists("output"):
        os.mkdir("output")
    run()
