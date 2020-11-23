# FogBus Containers Setup

## Requirements
- [Docker](https://docs.docker.com/get-docker/)

## Run

### Master

Backup your database if any.

Go to `containers/master`, use the following commands to build containers of FogBus Master and run,
```
cd containers/master
rm -rf data/db
docker-compose build
docker-compose up -d
```
Then, use your browser to visit FogBus Master at `127.0.0.1:80`. 
Both the initial account and password are `admin`.

 ### Worker
Go to `containers/worker`, use the following commands to build containers of FogBus Worker and run,
```
docker-compose build
docker-compose up -d
```
The address of Worker is at `127.0.0.1:81` by default. 

Congrats! Now you have containers of Fogbus Master and Worker. If you want to configure them, don't forget to create a network that they share together.