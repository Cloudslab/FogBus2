
build(){
  cd $1
  docker-compose \
      build \
      --build-arg  HTTP_PROXY="http://172.17.0.1:10801" \
      --build-arg  HTTPS_PROXY="http://172.17.0.1:10801" \
}

cd  build newLogger &
cd  build  newMaster &
cd  build newUser &
cd  build  newWorker &

cd sources/tasks && ./rebuild.sh
