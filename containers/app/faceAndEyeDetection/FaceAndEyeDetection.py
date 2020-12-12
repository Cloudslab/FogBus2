import cv2
import os
import sys
import json

dispW = 640
dispH = 480
flip = 2

filename = sys.argv[1]
cam = cv2.VideoCapture(filename) or 1

cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)
cam.set(cv2.CAP_PROP_FPS, 30)

print(cam.get(cv2.CAP_PROP_FPS))
print(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
face_cascade = cv2.CascadeClassifier('./cascade/haar-face.xml')
eye_cascade = cv2.CascadeClassifier('./cascade/haar-eye.xml')

facesRes = []
while True:
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


cam.release()

if not os.path.exists("output"):
    os.mkdir("output")

outPath = "./output/%s.json" % os.path.basename(filename)
f = open(outPath, "w")
f.write(json.dumps(facesRes))
f.close
cam.release()

print("[*] Processed %s. Result saved at %s" % (filename, outPath))

