# Prepare Docker Images

## Options

There are two ways of preparing docker images,

- [Build from scratch](#build-from-scratch)
- [Pull from Docker Hub](#pull-from-docker-hub)

For any of them, make sure you have  [Docker Environment](Requirements.md) 
before you start.
## Build from scratch

Use the following command build images from scratch,

```shell
$ pwd

/path/to/FogBus2/demo

$ python3.9 demo.py --buildAll

...
```
see [Demo](Demo.md) for more details.

## Pull from Docker Hub

Use the following commands to pull all the images from Docker Hub,
```shell
docker pull cloudslab/fogbus2-remote_logger && docker tag cloudslab/fogbus2-remote_logger fogbus2-remote_logger && 
docker pull cloudslab/fogbus2-master && docker tag cloudslab/fogbus2-master fogbus2-master && 
docker pull cloudslab/fogbus2-actor && docker tag cloudslab/fogbus2-actor fogbus2-actor && 
docker pull cloudslab/fogbus2-user && docker tag cloudslab/fogbus2-user fogbus2-user

```

Use the following commands to pull all `TaskExecutor` used in demo. You do not need to pull them if you plan to use your own `TaskExecutor`.
```
docker pull cloudslab/fogbus2-game_of_life0 && docker tag cloudslab/fogbus2-game_of_life0 fogbus2-game_of_life0 && 
docker pull cloudslab/fogbus2-game_of_life1 && docker tag cloudslab/fogbus2-game_of_life1 fogbus2-game_of_life1 && 
docker pull cloudslab/fogbus2-game_of_life2 && docker tag cloudslab/fogbus2-game_of_life2 fogbus2-game_of_life2 && 
docker pull cloudslab/fogbus2-game_of_life3 && docker tag cloudslab/fogbus2-game_of_life3 fogbus2-game_of_life3 && 
docker pull cloudslab/fogbus2-game_of_life4 && docker tag cloudslab/fogbus2-game_of_life4 fogbus2-game_of_life4 && 
docker pull cloudslab/fogbus2-game_of_life5 && docker tag cloudslab/fogbus2-game_of_life5 fogbus2-game_of_life5 && 
docker pull cloudslab/fogbus2-game_of_life6 && docker tag cloudslab/fogbus2-game_of_life6 fogbus2-game_of_life6 && 
docker pull cloudslab/fogbus2-game_of_life7 && docker tag cloudslab/fogbus2-game_of_life7 fogbus2-game_of_life7 && 
docker pull cloudslab/fogbus2-game_of_life8 && docker tag cloudslab/fogbus2-game_of_life8 fogbus2-game_of_life8 && 
docker pull cloudslab/fogbus2-game_of_life9 && docker tag cloudslab/fogbus2-game_of_life9 fogbus2-game_of_life9 && 
docker pull cloudslab/fogbus2-game_of_life10 && docker tag cloudslab/fogbus2-game_of_life10 fogbus2-game_of_life10 && 
docker pull cloudslab/fogbus2-game_of_life11 && docker tag cloudslab/fogbus2-game_of_life11 fogbus2-game_of_life11 && 
docker pull cloudslab/fogbus2-game_of_life12 && docker tag cloudslab/fogbus2-game_of_life12 fogbus2-game_of_life12 && 
docker pull cloudslab/fogbus2-game_of_life13 && docker tag cloudslab/fogbus2-game_of_life13 fogbus2-game_of_life13 && 
docker pull cloudslab/fogbus2-game_of_life14 && docker tag cloudslab/fogbus2-game_of_life14 fogbus2-game_of_life14 && 
docker pull cloudslab/fogbus2-game_of_life15 && docker tag cloudslab/fogbus2-game_of_life15 fogbus2-game_of_life15 && 
docker pull cloudslab/fogbus2-game_of_life16 && docker tag cloudslab/fogbus2-game_of_life16 fogbus2-game_of_life16 && 
docker pull cloudslab/fogbus2-game_of_life17 && docker tag cloudslab/fogbus2-game_of_life17 fogbus2-game_of_life17 && 
docker pull cloudslab/fogbus2-game_of_life18 && docker tag cloudslab/fogbus2-game_of_life18 fogbus2-game_of_life18 && 
docker pull cloudslab/fogbus2-game_of_life19 && docker tag cloudslab/fogbus2-game_of_life19 fogbus2-game_of_life19 && 
docker pull cloudslab/fogbus2-game_of_life20 && docker tag cloudslab/fogbus2-game_of_life20 fogbus2-game_of_life20 && 
docker pull cloudslab/fogbus2-game_of_life21 && docker tag cloudslab/fogbus2-game_of_life21 fogbus2-game_of_life21 && 
docker pull cloudslab/fogbus2-game_of_life22 && docker tag cloudslab/fogbus2-game_of_life22 fogbus2-game_of_life22 && 
docker pull cloudslab/fogbus2-game_of_life23 && docker tag cloudslab/fogbus2-game_of_life23 fogbus2-game_of_life23 && 
docker pull cloudslab/fogbus2-game_of_life24 && docker tag cloudslab/fogbus2-game_of_life24 fogbus2-game_of_life24 && 
docker pull cloudslab/fogbus2-game_of_life25 && docker tag cloudslab/fogbus2-game_of_life25 fogbus2-game_of_life25 && 
docker pull cloudslab/fogbus2-game_of_life26 && docker tag cloudslab/fogbus2-game_of_life26 fogbus2-game_of_life26 && 
docker pull cloudslab/fogbus2-game_of_life27 && docker tag cloudslab/fogbus2-game_of_life27 fogbus2-game_of_life27 && 
docker pull cloudslab/fogbus2-game_of_life28 && docker tag cloudslab/fogbus2-game_of_life28 fogbus2-game_of_life28 && 
docker pull cloudslab/fogbus2-game_of_life29 && docker tag cloudslab/fogbus2-game_of_life29 fogbus2-game_of_life29 && 
docker pull cloudslab/fogbus2-game_of_life30 && docker tag cloudslab/fogbus2-game_of_life30 fogbus2-game_of_life30 && 
docker pull cloudslab/fogbus2-game_of_life31 && docker tag cloudslab/fogbus2-game_of_life31 fogbus2-game_of_life31 && 
docker pull cloudslab/fogbus2-game_of_life32 && docker tag cloudslab/fogbus2-game_of_life32 fogbus2-game_of_life32 && 
docker pull cloudslab/fogbus2-game_of_life33 && docker tag cloudslab/fogbus2-game_of_life33 fogbus2-game_of_life33 && 
docker pull cloudslab/fogbus2-game_of_life34 && docker tag cloudslab/fogbus2-game_of_life34 fogbus2-game_of_life34 && 
docker pull cloudslab/fogbus2-game_of_life35 && docker tag cloudslab/fogbus2-game_of_life35 fogbus2-game_of_life35 && 
docker pull cloudslab/fogbus2-game_of_life36 && docker tag cloudslab/fogbus2-game_of_life36 fogbus2-game_of_life36 && 
docker pull cloudslab/fogbus2-game_of_life37 && docker tag cloudslab/fogbus2-game_of_life37 fogbus2-game_of_life37 && 
docker pull cloudslab/fogbus2-game_of_life38 && docker tag cloudslab/fogbus2-game_of_life38 fogbus2-game_of_life38 && 
docker pull cloudslab/fogbus2-game_of_life39 && docker tag cloudslab/fogbus2-game_of_life39 fogbus2-game_of_life39 && 
docker pull cloudslab/fogbus2-game_of_life40 && docker tag cloudslab/fogbus2-game_of_life40 fogbus2-game_of_life40 && 
docker pull cloudslab/fogbus2-game_of_life41 && docker tag cloudslab/fogbus2-game_of_life41 fogbus2-game_of_life41 && 
docker pull cloudslab/fogbus2-game_of_life42 && docker tag cloudslab/fogbus2-game_of_life42 fogbus2-game_of_life42 && 
docker pull cloudslab/fogbus2-game_of_life43 && docker tag cloudslab/fogbus2-game_of_life43 fogbus2-game_of_life43 && 
docker pull cloudslab/fogbus2-game_of_life44 && docker tag cloudslab/fogbus2-game_of_life44 fogbus2-game_of_life44 && 
docker pull cloudslab/fogbus2-game_of_life45 && docker tag cloudslab/fogbus2-game_of_life45 fogbus2-game_of_life45 && 
docker pull cloudslab/fogbus2-game_of_life46 && docker tag cloudslab/fogbus2-game_of_life46 fogbus2-game_of_life46 && 
docker pull cloudslab/fogbus2-game_of_life47 && docker tag cloudslab/fogbus2-game_of_life47 fogbus2-game_of_life47 && 
docker pull cloudslab/fogbus2-game_of_life48 && docker tag cloudslab/fogbus2-game_of_life48 fogbus2-game_of_life48 && 
docker pull cloudslab/fogbus2-game_of_life49 && docker tag cloudslab/fogbus2-game_of_life49 fogbus2-game_of_life49 && 
docker pull cloudslab/fogbus2-game_of_life50 && docker tag cloudslab/fogbus2-game_of_life50 fogbus2-game_of_life50 && 
docker pull cloudslab/fogbus2-game_of_life51 && docker tag cloudslab/fogbus2-game_of_life51 fogbus2-game_of_life51 && 
docker pull cloudslab/fogbus2-game_of_life52 && docker tag cloudslab/fogbus2-game_of_life52 fogbus2-game_of_life52 && 
docker pull cloudslab/fogbus2-game_of_life53 && docker tag cloudslab/fogbus2-game_of_life53 fogbus2-game_of_life53 && 
docker pull cloudslab/fogbus2-game_of_life54 && docker tag cloudslab/fogbus2-game_of_life54 fogbus2-game_of_life54 && 
docker pull cloudslab/fogbus2-game_of_life55 && docker tag cloudslab/fogbus2-game_of_life55 fogbus2-game_of_life55 && 
docker pull cloudslab/fogbus2-game_of_life56 && docker tag cloudslab/fogbus2-game_of_life56 fogbus2-game_of_life56 && 
docker pull cloudslab/fogbus2-game_of_life57 && docker tag cloudslab/fogbus2-game_of_life57 fogbus2-game_of_life57 && 
docker pull cloudslab/fogbus2-game_of_life58 && docker tag cloudslab/fogbus2-game_of_life58 fogbus2-game_of_life58 && 
docker pull cloudslab/fogbus2-game_of_life59 && docker tag cloudslab/fogbus2-game_of_life59 fogbus2-game_of_life59 && 
docker pull cloudslab/fogbus2-game_of_life60 && docker tag cloudslab/fogbus2-game_of_life60 fogbus2-game_of_life60 && 
docker pull cloudslab/fogbus2-game_of_life61 && docker tag cloudslab/fogbus2-game_of_life61 fogbus2-game_of_life61 && 

docker pull cloudslab/fogbus2-naive_formula0 && docker tag cloudslab/fogbus2-naive_formula0 fogbus2-naive_formula0 && 
docker pull cloudslab/fogbus2-naive_formula1 && docker tag cloudslab/fogbus2-naive_formula1 fogbus2-naive_formula1 && 
docker pull cloudslab/fogbus2-naive_formula2 && docker tag cloudslab/fogbus2-naive_formula2 fogbus2-naive_formula2 && 
docker pull cloudslab/fogbus2-naive_formula3 && docker tag cloudslab/fogbus2-naive_formula3 fogbus2-naive_formula3 && 

docker pull cloudslab/fogbus2-color_tracking && docker tag cloudslab/fogbus2-color_tracking fogbus2-color_tracking && 
docker pull cloudslab/fogbus2-face_detection && docker tag cloudslab/fogbus2-face_detection fogbus2-face_detection && 
docker pull cloudslab/fogbus2-eye_detection && docker tag cloudslab/fogbus2-eye_detection fogbus2-eye_detection && 
docker pull cloudslab/fogbus2-blur_and_p_hash && docker tag cloudslab/fogbus2-blur_and_p_hash fogbus2-blur_and_p_hash && 
docker pull cloudslab/fogbus2-ocr && docker tag cloudslab/fogbus2-ocr fogbus2-ocr

```
