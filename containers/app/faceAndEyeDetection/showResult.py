
import os
import sys
import cv2
import json


def show():
    filename = sys.argv[1]
    cap = cv2.VideoCapture(filename)
    f = open("./output/%s.json" % os.path.basename(filename), "r")
    facesRes = json.loads(f.read())
    f.close()

    frameNumber = 0
    while 1:
        ret, frame = cap.read()  # read the frame
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facesRes[frameNumber]

        frameNumber += 1
        for face in faces:
            (x, y, w, h) = face["face"]
            eyes = face["eyes"]

            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            for(x, y, w, h) in eyes:
                cv2.rectangle(roi_color, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.circle(roi_color, (int(x+w/2), int(y+h/2)), 3, (0, 255, 0), 1)
        cv2.imshow('cam', frame)  # show the frame
        cv2.moveWindow('cam', 0, 0)
        # read for 1 milisec and check if the 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()


if __name__ == "__main__":
    show()
