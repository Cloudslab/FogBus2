# MariaDB
MariaDB (a fork of MySQL) is supported and implemented in [containers/remoteLogger/sources/utils/remoteLogger/logger/database/mysqlDB.py](containers/remoteLogger/sources/utils/remoteLogger/logger/database/mysqlDB.py).

One can extend to other database or persistent storage with the abstract class [containers/remoteLogger/sources/utils/remoteLogger/logger/database/base.py](containers/remoteLogger/sources/utils/remoteLogger/logger/database/base.py)


## Quick Start
With [docker and python environment](../README.md#requirements) prepared, run following commands to prepare a running MariaDB,
```
$ cd containers/database/mariadb/
$ python3.9 configure.py --create --init

[2021-06-11 18:06:09,709][MariaDBSetup] Creating MariaDB: fogbus2-mariadb
fogbus2-mariadb
e6047dfd7167f1f8a6529e0929f5498f86e996f381c062e094a1d3b02a46891d
[2021-06-11 18:06:11,442][MariaDBSetup] Created MariaDB
    Container name: fogbus2-mariadb
    Password: passwordForRoot (You may change this in .env)
[2021-06-11 18:06:11,442][MariaDBSetup] Sleep 30 seconds waiting for creation...
[2021-06-11 18:06:42,534][MariaDBSetup] Your have many sql files under /Users/q/gits/newFogBus/containers/database/mariadb/sqlFiles,    
    [0] allDatabases-2021-05-23-12:06:47.154362.sql
    [1] allDatabases.sql
Which one to use(number):
1
[2021-06-11 18:08:31,65][MariaDBSetup] Initializing database with file:
    /Users/q/gits/newFogBus/containers/database/mariadb/sqlFiles/allDatabases.sql
[2021-06-11 18:08:32,19][MariaDBSetup] Initialized MariaDb
```

## Usage

```
$ python3.9 configure.py -h
usage: configure.py [-h] [--create | --no-create] [--init | --no-init] [--backup | --no-backup]

MariaDB Setup

optional arguments:
  -h, --help            show this help message and exit
  --create, --no-create
                        Create MariaDB container (default: False)
  --init, --no-init     Initialize MariaDB databases (default: False)
  --backup, --no-backup
                        Backup MariaDB databases (default: False)
```