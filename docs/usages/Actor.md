# Actor Usage

The source code of `Actor` locates at `containers/actor/sources/actor.py`. Normally, the component runs in container, however, the usages of it can be printed with command,
```
$ python actor.py -h
usage: actor.py [-h] [--bindIP BindIP] [--bindPort [BindPort]] [--masterIP MasterIP] [--masterPort [MasterPort]] [--remoteLoggerIP RemoteLoggerIP]
                [--remoteLoggerPort [RemoteLoggerPort]] [--containerName [ContainerName]] [--verbose [Verbose]] [--actorResources [ActorResources]]

Actor

optional arguments:
  -h, --help            show this help message and exit
  --bindIP BindIP       User ip.
  --bindPort [BindPort]
                        Bind port
  --masterIP MasterIP   Master ip.
  --masterPort [MasterPort]
                        Master port
  --remoteLoggerIP RemoteLoggerIP
                        Remote logger ip.
  --remoteLoggerPort [RemoteLoggerPort]
                        Remote logger port
  --containerName [ContainerName]
                        container name
  --verbose [Verbose]   Reference python logging level, from 0 to 50 integer to show log
  --actorResources [ActorResources]
                        Actor resources in Json string format
```
Here is the detailed explanation,
|Argument|Explanation|E.g.|
|:-------------|:-------------|:-------------|
|--bindIP|The IP used to communicate with other components.|127.0.0.1|
|--bindPort|The Port used to communicate with other components.|5001|
|--verbose|Numeric Log level. Refers to [Python official document](https://docs.python.org/3/library/logging.html#levels).|20|
|--containerName|Initial container name. This is needed to automatically change the container's name when the name changing of container requires this name to identify the container.|TempContainerName|
|--remoteLoggerIP|The IP of `RemoteLogger`.|127.0.0.1|
|--remoteLoggerPort|The Port of `RemoteLogger`.|5000|
|--masterIP|The IP of `Master`.|127.0.0.1|
|--masterPort|The Port of `Master`.|5001|
