build() {

  cd $1
  docker-compose \
    build \
    --build-arg HTTP_PROXY="http://172.17.0.1:10801" \
    --build-arg HTTPS_PROXY="http://172.17.0.1:10801"

}

build newLogger &
build newMaster &
build newUser &
build newWorker &
cd newWorker/sources/tasks && ./rebuild.sh
