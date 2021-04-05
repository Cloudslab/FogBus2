build() {
  cd $1
  docker-compose \
    build
  cd ..}
for d in */; do
  echo "[*] Building $d ..."
  build $d
done
