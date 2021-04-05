# Remote Logger Usage

The source code of `RemoteLogger` locates at `containers/remoteLogger/sources/remoteLogger.py`. Normally, the component runs in container, however, the usages of it can be printed with command,
```
$ python remoteLogger.py -h
usage: remoteLogger.py [-h] [--bindIP BindIP] [--bindPort [ListenPort]] [--verbose [Verbose]] [--containerName [ContainerName]]

Remote Logger

optional arguments:
  -h, --help            show this help message and exit
  --bindIP BindIP       Remote logger ip.
  --bindPort [ListenPort]
                        Remote logger port.
  --verbose [Verbose]   Reference python logging level, from 0 to 50 integer to show log
  --containerName [ContainerName]
                        container name
```
Here is the detailed explanation,
|Argument|Explanation|E.g.|
|:-------------|:-------------|:-------------|
|--bindIP|The IP used to communicate with other components.|127.0.0.1|
|--bindPort|The Port used to communicate with other components.|5000|
|--verbose|Numeric Log level. Refers to [Python official document](https://docs.python.org/3/library/logging.html#levels).|20|
|--containerName|Initial container name. This is needed to automatically change the container's name when the name changing of container requires this name to identify the container.|TempContainerName|
