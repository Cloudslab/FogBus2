# User Usage

The source code of `User` locates at `containers/user/sources/user.py`. The usages of it can be printed with command,
```
$ python user.py -h
usage: user.py [-h] [--bindIP BindIP] [--bindPort [BindPort]] [--masterIP MasterIP] [--masterPort [MasterPort]] [--remoteLoggerIP RemoteLoggerIP]
               [--remoteLoggerPort [RemoteLoggerPort]] [--applicationName ApplicationName] [--applicationLabel ApplicationLabel] [--containerName [ContainerName]]
               [--videoPath [VideoPath]] [--showWindow | --no-showWindow] [--verbose [Verbose]] [--golInitText [GameOfLifeInitialWorldText]]

User

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
  --applicationName ApplicationName
                        Application Name
  --applicationLabel ApplicationLabel
                        e.g. 480 or 720
  --containerName [ContainerName]
                        container name
  --videoPath [VideoPath]
                        /path/to/video.mp4
  --showWindow, --no-showWindow
                        Show window or not (default: True)
  --verbose [Verbose]   Reference python logging level, from 0 to 50 integer to show log
  --golInitText [GameOfLifeInitialWorldText]
                        GameOfLife initial world text
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
|--applicationName|Which application to run. `FaceDetection`, `FaceAndEyeDetection`, `ColorTracking`, `VideoOCR`, `GameOfLifeSerialized`, `GameOfLifeParallelized`, or `GameOfLifePyramid`. `GameOfLifeParallelized` runs all tasks in parallel. `GameOfLifePyramid` runs tasks which depend on others with a pyramid relationship. And `GameOfLifeSerialized` runs tasks serialized. |FaceDetection|
|--applicationLabel|Label of application, developers can parse this for the specific application need. For example, for application `FaceDetection`, this label can be a number, `720`, which indicates the resolution of each frame.|480|
|--videoPath|For application `FaceDetection`, `FaceAndEyeDetection`, `ColorTracking`, and `VideoOCR`, if this argument is not empty, the application consider the value to be the path to a video. The video will be the input.|/path/to/video.mp4|
|--golInitText|For application `GameOfLifeSerialized`, `GameOfLifeParallelized`, and `GameOfLifePyramid`, this will be the test of the initial world.|FogBus2|
