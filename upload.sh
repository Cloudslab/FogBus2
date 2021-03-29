#! /bin/sh
set -e

hostsFilename='hosts'

handle(){
  host=$1
  echo "$host";
  scp code.tar "$host:";
  ssh "$host" "mkdir -p ~/new  && tar xf ~/code.tar -C ~/new" < /dev/null;
  echo "[*] $host done."
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
