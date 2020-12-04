# Authorised by Mohammad Goudarzi

import cv2

dispW=640
dispH=480
flip=2

cam=cv2.VideoCapture(0) # o or 1

cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)
cam.set(cv2.CAP_PROP_FPS, 30)

print(cam.get(cv2.CAP_PROP_FPS))
print(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
face_cascade=cv2.CascadeClassifier('../data/cascade/haar-face.xml')
eye_cascade=cv2.CascadeClassifier('../data/cascade/haar-eye.xml')
while True:
    ret, frame=cam.read() # read the frame
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces=face_cascade.detectMultiScale(gray,1.3,5)
    
    
    for(x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

        roi_gray=gray[y:y+h,x:x+w]
        roi_color=frame[y:y+h,x:x+w]
        eyes=eye_cascade.detectMultiScale(roi_gray)

        for(x,y,w,h) in eyes:
            cv2.rectangle(roi_color,(x,y),(x+w,y+h),(0,0,255),2)
            cv2.circle(roi_color,(int(x+w/2),int(y+h/2)),3,(0,255,0),1)
    cv2.imshow('cam',frame) # show the frame
    cv2.moveWindow('cam',0,0)

    if cv2.waitKey(1) & 0xFF==ord('q'): # read for 1 mili-second and check if the 'q' is pressed
        break
cam.release()
cv2.destroyAllWindow()
