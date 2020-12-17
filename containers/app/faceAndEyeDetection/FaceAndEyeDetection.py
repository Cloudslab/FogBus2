import cv2
import os
import sys
import json
import signal


userQuit = False


def signal_handler(signal, frame):
    userQuit = True
    print("[*] Quit.")


def run():

    dispW = 640
    dispH = 480
    flip = 2

    if len(sys.argv) < 2:
        isWebCamera = True

    if isWebCamera:
        filename = "./output/WebCamera.mp4"
        cam = cv2.VideoCapture(0)
        out = cv2.VideoWriter(
            filename,
            cv2.VideoWriter_fourcc('m', 'p', '4', 'v'),
            30,
            (dispW, dispH),
            True)

    else:
        filename = sys.argv[1]
        cam = cv2.VideoCapture(filename)  # o or 1

    print("[*] Processing %s ..." % filename)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)
    cam.set(cv2.CAP_PROP_FPS, 30)

    print(cam.get(cv2.CAP_PROP_FPS))
    print(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')
    eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

    facesRes = []
    while True and not userQuit:
        ret, frame = cam.read()  # read the frame
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        faceTmp = []
        for(x, y, w, h) in faces:
            tmp = {"face": [int(x), int(y), int(w), int(h)], "eyes": []}

            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)

            for(x, y, w, h) in eyes:
                tmp["eyes"].append([int(x), int(y), int(w), int(h)])

            faceTmp.append(tmp)

        facesRes.append(faceTmp)

        if isWebCamera:
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                eyes = eye_cascade.detectMultiScale(roi_gray)

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                for(x, y, w, h) in eyes:
                    cv2.rectangle(roi_color, (x, y),
                                  (x+w, y+h), (0, 0, 255), 2)
                    cv2.circle(roi_color, (int(x+w/2), int(y+h/2)),
                               3, (0, 255, 0), 1)
            out.write(frame)

    cam.release()
    out.release()

    outPath = "./output/%s.json" % os.path.basename(filename)
    f = open(outPath, "w")
    f.write(json.dumps(facesRes))
    f.close

    print("[*] Processed %s. Result saved at %s" % (filename, outPath))


if __name__ == "__main__":
    if not os.path.exists("output"):
        os.mkdir("output")

    signal.signal(signal.SIGINT, signal_handler)
    run()
