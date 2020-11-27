# FogBus Container Setup

## Support Architecture
- x86-64
- arm64
- armhf

## Requirements
- [Docker](https://docs.docker.com/get-docker/)

## Run
### Master

Go to `containers/master`, use the following commands to build containers of FogBus Master and run. Make sure you have backup of `container/master/data/db`.
```
cd containers/master
rm -rf data/db
docker-compose up -d
```
Then, use your browser to visit FogBus Master at `127.0.0.1:80`. 
Both the initial account and password are `admin`.

 ### Worker
Go to `containers/worker`, use the following commands to build containers of FogBus Worker and run,
```
docker-compose up -d
```
The address of Worker is at `127.0.0.1:81` by default. 

Congrats! Now you have containers of Fogbus Master and Worker. If you want to configure them, don't forget to create a network that they can access each other.