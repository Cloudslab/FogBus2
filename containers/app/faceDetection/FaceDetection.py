# Authorised by Mohammad Goudarzi

import cv2
# The model frontalface is only for frontal face

#print(cv2.__version__)
dispW=640
dispH=480
flip=2
#camSet='nvarguscamerasrc !  video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method='+str(flip)+' ! video/x-raw, width='+str(dispW)+', height='+str(dispH)+', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
#cam=cv2.VideoCapture(camSet) #cam for pi camera
cam=cv2.VideoCapture(0) # o or 1

cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)
cam.set(cv2.CAP_PROP_FPS, 30)

print(cam.get(cv2.CAP_PROP_FPS))
print(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
face_cascade=cv2.CascadeClassifier('../data/cascade/haar-face.xml')
while True:
    ret, frame=cam.read() # read the frame
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces=face_cascade.detectMultiScale(gray,1.3,5)
    
    for(x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
    cv2.imshow('cam',frame) # show the frame
    cv2.moveWindow('cam',0,0)
    if cv2.waitKey(1) & 0xFF==ord('q'): # read for 1 milisec and check if the 'q' is pressed
        break
cam.release()
cv2.destroyAllWindow()
