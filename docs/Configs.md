# Configs

Some configs for different components may be the same, however, for better distribution the duplicated configs are copied to each components sources folder, which will be copied to the image in building phase.

## Remote Logger

### Ports 
Modify the [containers/remoteLogger/sources/.env](../containers/remoteLogger/sources/.env) to set component ports ranges,
```
$ cat containers/remoteLogger/sources/.env 
REMOTE_LOGGER_PORT_RANGE=5000-5000
MASTER_PORT_RANGE=5001-5010
ACTOR_PORT_RANGE=50000-50100
USER_PORT_RANGE=50101-50200
TASK_EXECUTOR_PORT_RANGE=50201-60000
```

### MariaDB

Modify the [containers/remoteLogger/sources/.mysql.env ](../containers/remoteLogger/sources/.mysql.env ) to set MariaDB database environments,
```
$ cat containers/remoteLogger/sources/.mysql.env 
HOST=127.0.0.1
PORT=3306
USER=root
PASSWORD=passwordForRoot
```

## Master

### Ports 
Modify the [containers/master/sources/.env](../containers/master/sources/.env) to set component ports ranges,
```
$ cat containers/master/sources/.env 
REMOTE_LOGGER_PORT_RANGE=5000-5000
MASTER_PORT_RANGE=5001-5010
ACTOR_PORT_RANGE=50000-50100
USER_PORT_RANGE=50101-50200
TASK_EXECUTOR_PORT_RANGE=50201-60000
```

### MariaDB

Modify the [containers/master/sources/.mysql.env ](../containers/master/sources/.mysql.env ) to set MariaDB database environments,
```
$ cat containers/master/sources/.mysql.env 
HOST=127.0.0.1
PORT=3306
USER=root
PASSWORD=passwordForRoot
```


## Actor

### Ports 
Modify the [containers/actor/sources/.env](../containers/actor/sources/.env) to set component ports ranges,
```
$ cat containers/actor/sources/.env 
REMOTE_LOGGER_PORT_RANGE=5000-5000
MASTER_PORT_RANGE=5001-5010
ACTOR_PORT_RANGE=50000-50100
USER_PORT_RANGE=50101-50200
TASK_EXECUTOR_PORT_RANGE=50201-60000
```

## Task Executor

### Ports 
Modify the [containers/taskExecutor/sources/.env](../containers/taskExecutor/sources/.env) to set component ports ranges,
```
$ cat containers/taskExecutor/sources/.env 
REMOTE_LOGGER_PORT_RANGE=5000-5000
MASTER_PORT_RANGE=5001-5010
ACTOR_PORT_RANGE=50000-50100
USER_PORT_RANGE=50101-50200
TASK_EXECUTOR_PORT_RANGE=50201-60000
```

## User

### Ports 
Modify the [containers/user/sources/.env](../containers/user/sources/.env) to set component ports ranges,
```
$ cat containers/user/sources/.env 
REMOTE_LOGGER_PORT_RANGE=5000-5000
MASTER_PORT_RANGE=5001-5010
ACTOR_PORT_RANGE=50000-50100
USER_PORT_RANGE=50101-50200
TASK_EXECUTOR_PORT_RANGE=50201-60000
```

## Hosts Information

Modify the [config/host/hostIP.csv](../config/host/hostIP.csv) to set hosts' information.
```
$ cat config/host/hostIP.csv 
hostname, publicIP
oracle1, 168.138.9.91
oracle2, 168.138.10.94
oracle3, 168.138.15.110
nectar1, 45.113.235.222
nectar2, 45.113.232.187
nectar3, 45.113.232.245
rpi1,
rpi2,
```

## Wireguard Network

Modify the [config/network.env](../config/network.env) to set subnet range for [Wireguard](./Wireguard.md).
```
$ cat config/network.env    
WG_NET=192.0.0.0/24
WG_PORT=4999
```
