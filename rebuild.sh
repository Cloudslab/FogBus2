#! /bin/sh
set -e

hostsFilename='hosts'

handle(){
  host=$1
  echo "$host";
  ssh "$host" "cd ~/new/containers/  && ./rebuild.sh > /dev/null 2>&1" < /dev/null;
  echo "[======================]"
  echo "[*] $host done."
  echo "[======================]"
}

loop(){
  hostsFilename=$1
  while read -r host;
  do
    handle "$host" &
  done < "$hostsFilename"
}

git archive -o code.tar HEAD --format=tar

loop "$hostsFilename"
