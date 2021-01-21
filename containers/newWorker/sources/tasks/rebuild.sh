
build(){
docker-compose build \
    --build-arg  HTTP_PROXY="http://172.17.0.1:10801" \
    --build-arg  HTTPS_PROXY="http://172.17.0.1:10801"
}

cd BlurAndPHash && build
cd  ../ColorTracking && build
cd  ../EyeDetection && build
cd  ../FaceDetection && build
cd  ../OCR && build
