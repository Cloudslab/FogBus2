import cv2
import sys
import os
import json
import signal

userQuit = False


def signal_handler(signal, frame):
    userQuit = True
    print("[*] Quit.")


def run():
    isWebCamera = False
    # The model frontalface is only for frontal face

    # print(cv2.__version__)
    dispW = 640
    dispH = 480
    flip = 2
    #camSet='nvarguscamerasrc !  video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method='+str(flip)+' ! video/x-raw, width='+str(dispW)+', height='+str(dispH)+', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
    # cam=cv2.VideoCapture(camSet) #cam for pi camera
    if len(sys.argv) < 2:
        isWebCamera = True

    if isWebCamera:
        filename = "WebCamera"
        cam = cv2.VideoCapture(0)
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
    boxesRes = []
    while True and not userQuit:
        ret, frame = cam.read()  # read the frame
        
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        tmp = []
        for(x, y, w, h) in faces:
            tmp.append([int(x), int(y), int(w), int(h)])
        boxesRes.append(tmp)

        if isWebCamera:
            for(x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.imshow('cam', frame)  # show the frame
            cv2.moveWindow('cam', 0, 0)
            # read for 1 milisec and check if the 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    if not os.path.exists("output"):
        os.mkdir("output")

    outPath = "./output/%s.json" % os.path.basename(filename)
    f = open(outPath, "w")
    f.write(json.dumps(boxesRes))
    f.close
    cam.release()

    print("[*] Processed %s. Result saved at %s" % (filename, outPath))


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    run()
