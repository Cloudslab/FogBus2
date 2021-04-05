#! /bin/sh
set -e

hostsFilename='hosts'

handle(){
  host=$1
  echo "$host";
  scp "env.sh" "$host:new/env.sh"
  ssh "$host" "bash ~/new/env.sh"
}

loop(){
  hostsFilename=$1
  while read -r host;
  do
    handle "$host"
  done < "$hostsFilename"
}

loop "$hostsFilename"
