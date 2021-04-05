#! /bin/sh
set -e

hostsFilename='hosts'

handle(){
  host=$1
  echo "$host";
  ssh "$host" "cd ~/new/demo/  && python3.9 demo.py --buildAll";
  echo "[======================]"
  echo "[*] $host done."
  echo "[======================]"
}

loop(){
  hostsFilename=$1
  while read -r host;
  do
    handle "$host"
  done < "$hostsFilename"
}

loop "$hostsFilename"
