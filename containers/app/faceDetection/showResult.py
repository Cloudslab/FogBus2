
import os
import sys
import cv2
import json


def show():
    filename = sys.argv[1]
    cap = cv2.VideoCapture(filename)
    f = open("./output/%s.json" % os.path.basename(filename), "r")
    boxesRes = json.loads(f.read())
    f.close()

    frameNumber = 0
    while 1:
        ret, frame = cap.read()  # read the frame
        if not ret:
            break
        boxes = boxesRes[frameNumber]
        frameNumber += 1
        for(x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.imshow('cam', frame)  # show the frame
        cv2.moveWindow('cam', 0, 0)
        # read for 1 milisec and check if the 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()


if __name__ == "__main__":
    show()
