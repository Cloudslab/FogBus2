
build(){
docker-compose \
    build \
    --build-arg  HTTP_PROXY="http://172.17.0.1:10801" \
    --build-arg  HTTPS_PROXY="http://172.17.0.1:10801" \

}

cd newLogger && build
cd  ../newMaster && build
cd  ../newUser && build
cd  ../newWorker && build

cd sources/tasks && ./rebuild.sh
