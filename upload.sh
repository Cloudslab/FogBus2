#! /bin/sh
set -e

hostsFilename='hosts'

handle() {
  host=$1
  echo "$host"
  scp code.tar "$host:"
  ssh "$host" "mkdir -p ~/fogbus2  && tar  xf  ~/code.tar --exclude='containers/database/mariadb/mysql' -C ~/fogbus2" <  /dev/null;
#  ssh "$host" "mkdir -p ~/fogbus2  && tar xf ~/code.tar -C ~/fogbus2"
  echo "[*] $host done."
}

loop() {
  hostsFilename=$1
  while read -r host; do
    handle "$host"
  done <"$hostsFilename"
}

git archive -o code.tar HEAD --format=tar

loop "$hostsFilename"
