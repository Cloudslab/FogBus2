# Master Usage

The source code of `Master` locates at `containers/master/sources/master.py`. Normally, the component runs in container, however, the usages of it can be printed with command,
```
$ python master.py -h        
usage: master.py [-h] [--bindIP BindIP] [--bindPort [ListenPort]] [--remoteLoggerIP [RemoteLoggerIP]] [--remoteLoggerPort [RemoteLoggerPort]]
                 [--schedulerName [SchedulerName]] [--createdByIP [CreatedByIP]] [--createdByPort [CreatedByPort]] [--minimumActors MinimumActors]
                 [--estimationThreadNum [EstimationThreadNumber]] [--databaseType [DatabaseType]] [--verbose [Verbose]]
                 [--profileDataRatePeriod [ProfileDataRatePeriod]] [--taskExecutorCoolPeriod [TaskExecutorCoolPeriod Reusability]]
                 [--containerName [ContainerName]]

Master

optional arguments:
  -h, --help            show this help message and exit
  --bindIP BindIP       Master ip.
  --bindPort [ListenPort]
                        Master port.
  --remoteLoggerIP [RemoteLoggerIP]
                        Remote logger ip.
  --remoteLoggerPort [RemoteLoggerPort]
                        Remote logger port
  --schedulerName [SchedulerName]
                        Scheduler name
  --createdByIP [CreatedByIP]
                        IP of the Master who asked to create this new Master
  --createdByPort [CreatedByPort]
                        Port of the Master who asked to create this new Master
  --minimumActors MinimumActors
                        minimum actors needed
  --estimationThreadNum [EstimationThreadNumber]
                        Estimation thread number
  --databaseType [DatabaseType]
                        Database type, e.g., MariaDB
  --verbose [Verbose]   Reference python logging level, from 0 to 50 integer to show log
  --profileDataRatePeriod [ProfileDataRatePeriod]
                        Period for Master to profile data rate and latency. In seconds. Set to 0 to disable
  --taskExecutorCoolPeriod [TaskExecutorCoolPeriod (Reusability)]
                        How many seconds does task executor wait after finishes task
  --containerName [ContainerName]
                        container name

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
|--schedulerName|The policy of scheduler to use. NSGA2, NSGA3, or OHNSGA|OHNSGA|
|--createdByIP|If this `Master` is created by `otherMaster`, set the IP of `otherMaster`. Otherwise, leave it blank. This  parameter is often used by scaler automatically.|192.168.0.1|
|--createdByPort|Port of `otherMaster`.|5001|
|--minimumActors|For experiment. `Master` responds `User` only when there is at least this number of registered `Actor`s|3|
|--estimationThreadNum|The thread number for scheduler to run fitness function, 8 by default|16|
|--taskExecutorCoolPeriod|Seconds of the period for TaskExecutor to wait after it has finished the previous task. If it receives any placement during the period, it is renewed; otherwise, it exits. Set to 0 to disable this so call reusability. |600|
|--profileDataRatePeriod|Seconds of the period for Master to profile data rate and latency between two instances. This profiling will wait until there are no less registered actors than `--minActors`|86400|
