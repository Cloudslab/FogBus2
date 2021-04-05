#!/bin/bash

if [ $1 ]; then
  docker stop $(docker ps -a -q --filter="name=$1")
  docker rm $(docker ps -a -q --filter="name=$1")
else
  docker stop $(docker ps -a -q)
  docker rm $(docker ps -a -q)
fi
