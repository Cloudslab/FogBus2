# Demo
This demo is for user to easily play around. 
Make sure [docker and python environment](Requirements.md) 
are prepared.

## Build Docker Images
This may take long time to run. 
```shell
$ pwd

/path/to/FogBus2/demo

$ python3.9 demo.py --buildAll

...
```
You can also build images with proxy using `python3.9 demo.py --buildAll --buildProxy http://127.0.0.1:8080`.

You may want to cross build images for other platforms, the following commands shows an example of building all images for `linux/amd64`, `linux/arm64`, `linux/arm/v7`, and `linux/arm/v6`. After which, push it to [https://hub.docker.com/orgs/cloudslab/repositories](https://hub.docker.com/orgs/cloudslab/repositories),
```shell
$ pwd

/path/to/FogBus2/demo

$ python demo.py --buildAll --platforms linux/amd64,linux/arm64,linux/arm/v7,linux/arm/v6 --dockerHubUsername cloudslab --push

...
```
If you don't want to push to your Docker Hub, do not set `--push`. 

Before pushing any built image to Docker Hub, run `docker login`. 

Before cross building, run `docker run --privileged --rm tonistiigi/binfmt --install all`. Moreover, if you use `docker buildx` to build for cross platforms with builder using ***mutiple nodes***(different architectures), the following command may be used to 
build and join a node using proxy during building.
```shell
docker buildx create --name multiNodesBuilder

DOCKER_HOST=ssh://user@host docker buildx create --append --name multiNodesBuilder --node OneNode --platform=linux/arm/v7  --driver-opt env.http_proxy=http://127.0.0.1:8080 --driver-opt env.https_proxy=http://127.0.0.1:8080 --buildkitd-flags '--allow-insecure-entitlement network.host'

```

***NOTE: You need to rebuild images after changing any code***

Alternatively, you can pull the pre-built images [from our Docker Hub](PrepareDockerImages.md#pull-from-docker-hub).


## Quick Start
With [docker and python environment](../README.md#requirements) prepared, run following commands to run default demo,
```
$ cd demo
$ python demo.py --default

Creating remotelogger_fogbus2-remote_logger_run ... done
[2021-06-11 20:25:28,136][TempDebugLogger] Listening at ('127.0.0.1', 5000)
[2021-06-11 20:25:28,274][RemoteLogger-?_127.0.0.1-5000] Running ...
Creating master_fogbus2-master_run ... done
[2021-06-11 20:25:33,407][TempDebugLogger] Listening at ('127.0.0.1', 5001)
[2021-06-11 20:25:33,505][Master-?_127.0.0.1-5001] Serving...
Creating actor_fogbus2-actor_run ... done
[2021-06-11 20:25:37,457][TempDebugLogger] Listening at ('127.0.0.1', 50000)
[2021-06-11 20:25:37,479][Actor-?_127.0.0.1-50000] Profiling...
[2021-06-11 20:25:38,299][Actor-?_127.0.0.1-50000] Registering...
[2021-06-11 20:25:38,346][Actor-1_127.0.0.1-50000_Master-?_127.0.0.1-5001] Registered, running...
...
```
By default, demo script runs `FaceDetection`, you can also run other applications, see [Usage](#usage).
## Configs

To modify configs, see [Configs](./Configs.md).

## Usage

```
$  python demo.py -h

usage: demo.py [-h] [--buildProxy [BuildProxy]] [--buildAll | --no-buildAll] [--buildActorImage | --no-buildActorImage]
               [--buildMasterImage | --no-buildMasterImage] [--buildUserImage | --no-buildUserImage]
               [--buildRemoteLoggerImage | --no-buildRemoteLoggerImage] [--buildTaskExecutorImage | --no-buildTaskExecutorImage]
               [--default | --no-default] [--applicationName ApplicationName] [--applicationLabel ApplicationLabel] [--videoPath VideoPath]
               [--platforms Platforms] [--dockerHubUsername DockerHubUsername] [--showWindow | --no-showWindow] [--uploadCode | --no-uploadCode]
               [--buildRemoteImages | --no-buildRemoteImages] [--withRPi | --no-withRPi] [--onlyRPi | --no-onlyRPi] [--push | --no-push]
               [--bindIP [BindIP]] [--verbose [Verbose]]

Demo

optional arguments:
  -h, --help            show this help message and exit
  --buildProxy [BuildProxy]
                        Proxy used when building images
  --buildAll, --no-buildAll
                        Build images of RemoteLogger, Master, Actor, TaskExecutor, and User (default: False)
  --buildActorImage, --no-buildActorImage
                        Build Actor image or not (default: False)
  --buildMasterImage, --no-buildMasterImage
                        Build Master image or not (default: False)
  --buildUserImage, --no-buildUserImage
                        Build User image or not (default: False)
  --buildRemoteLoggerImage, --no-buildRemoteLoggerImage
                        Build RemoteLogger image or not (default: False)
  --buildTaskExecutorImage, --no-buildTaskExecutorImage
                        Build TaskExecutor image or not (default: False)
  --default, --no-default
                        Run default demonstration with all components running locally.Showing FaceAndEyeDetection and 1 container each component.
                        (default: False)
  --applicationName ApplicationName
                        Application Name
  --applicationLabel ApplicationLabel
                        e.g. 480 or 720
  --videoPath VideoPath
                        /path/to/video.mp4
  --platforms Platforms
                        If you want to build images for cross platforms, set your platforms here.E.g.,
                        linux/amd64,linux/arm64,linux/arm/v7,linux/arm/v6. You may need to run the following before it: docker run --privileged --rm
                        tonistiigi/binfmt --install all
  --dockerHubUsername DockerHubUsername
                        If you want to push built images to your docker hub, set your docker hub username here. Otherwise, leave it to be empty string
  --showWindow, --no-showWindow
                        Show window or not (default: True)
  --uploadCode, --no-uploadCode
                        Upload Code to RPi or not (default: False)
  --buildRemoteImages, --no-buildRemoteImages
                        Build images on RPi or not (default: False)
  --withRPi, --no-withRPi
                        Demo with Raspberry Pi or not (default: False)
  --onlyRPi, --no-onlyRPi
                        Demo only with Raspberry Pi (default: False)
  --push, --no-push     Push images to Docker Hub or not (default: False)
  --bindIP [BindIP]     Which IP to use
  --verbose [Verbose]   Reference python logging level, from 0 to 50 integer to show log

```