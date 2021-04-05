# Add Database Support

In this guide, we will see how to add a new database support. We will take 
`Applications` and `Tasks` databases of `Master` for example. The database 
we are going to support is [Oracle Autonomous Database](https://www.oracle.com/hk/autonomous-database/).

## Requirements

- For the convenience of debugging, [Python3.9](../../README.md#optional) environment is recommended. You may also want to install the libraries, `python3.9 -m pip install -r containers/master/sources/requirements.txt`.

- The test platform is Ubuntu 20.04.

- [tree](http://mama.indstate.edu/users/ice/tree/) is optional for printing file tree structure.

## Provision Oracle Autonomous Database (ADB)
**First**, an available ADB is required. You can provision one in your [oracle cloud console](https://www.oracle.com/cloud/sign-in.html).
 Using a database name `ADB_NAME`, a username `ADB_USERNAME`, and a password `ADB_PASSWORD`.

**Second**, download the wallet following steps `DB Connection` -> `Download Wallet` with a password `ADB_PASSWORD`



## Download Oracle Instant Client
**Third**, download [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client/downloads.html), and set it up with your wallet file following [these steps](https://www.oracle.com/database/technologies/appdev/python/quickstartpython.html). 

*We tested the code using instantclient_21_1, but the steps will be similar for other version of oracle instant clients.*

You need to extract all the files of wallet to `instant_client/network/admin`, so it looks like, 
```
$ pwd

/path/to/instantclient

$ tree

.
├── BASIC_LICENSE
├── BASIC_README
├── adrci
├── genezi
├── libclntsh.dylib -> libclntsh.dylib.19.1
├── libclntsh.dylib.10.1 -> libclntsh.dylib.19.1
├── libclntsh.dylib.11.1 -> libclntsh.dylib.19.1
├── libclntsh.dylib.12.1 -> libclntsh.dylib.19.1
├── libclntsh.dylib.18.1 -> libclntsh.dylib.19.1
├── libclntsh.dylib.19.1
├── libclntshcore.dylib.19.1
├── libnnz19.dylib
├── libocci.dylib -> libocci.dylib.19.1
├── libocci.dylib.10.1 -> libocci.dylib.19.1
├── libocci.dylib.11.1 -> libocci.dylib.19.1
├── libocci.dylib.12.1 -> libocci.dylib.19.1
├── libocci.dylib.18.1 -> libocci.dylib.19.1
├── libocci.dylib.19.1
├── libociei.dylib
├── libocijdbc19.dylib
├── liboramysql19.dylib
├── network
│   └── admin
│       ├── README
│       ├── cwallet.sso
│       ├── ewallet.p12
│       ├── keystore.jks
│       ├── ojdbc.properties
│       ├── sqlnet.ora
│       ├── tnsnames.ora
│       └── truststore.jks
├── ojdbc8.jar
├── ucp.jar
├── uidrvci
└── xstreams.jar

2 directories, 33 files
```

**Fourth**, [add Instant Client to the runtime link path](https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html#oracle-instant-client-zip-files),
```
sudo sh -c "echo /path/to/instantclient > /etc/ld.so.conf.d/oracle-instantclient.conf"
sudo ldconfig
```

## Support ADB
**Fifth**, add `containers/master/sources/utils/master/application/database/adb.py` with content,

```python
import cx_Oracle
import os
from abc import abstractmethod
from json import loads
from typing import Dict

from .base import BaseDatabase
from ..base import Application
from ..task.base import Task
from ..task.dependency.base import TaskWithDependency


class OracleAutonomousDatabase(BaseDatabase):

    def __init__(
            self,
            user: str = ADB_USERNAME,
            password: str = ADB_PASSWORD,
            dsn: str = ADB_NAME_high,
            **kwargs):
        BaseDatabase.__init__(self)

        connection = cx_Oracle.connect(
            user=user,
            password=password,
            dsn=dsn)

        # Obtain a cursor
        self.cursor = connection.cursor()

    def readTasks(self) -> Dict[str, Task]:
        """
        Get tasks from database
        :return: A list of task objects
        """
        sql = 'SELECT NAME FROM ( \
                SELECT t.*, ROWID \
                FROM ADB_USERNAME.TASKS t \
            )'
        self.cursor.execute(sql)
        tasks = {}
        rows = self.cursor.fetchall()
        for row in rows:
            taskName = row[0]
            tasks[taskName] = Task(taskName)
        return tasks

    def writeTask(self, taskName: str):
        """
        Save a task in database
        :param taskName: task name
        :return: None
        """
        pass

    def readApplications(self) -> Dict[str, Application]:
        """
        Read applications from database
        :return: An application list. Key is application name in str and
        value is application object
        """
        sql = 'SELECT * FROM ( \
                SELECT t.* \
                FROM ADB_USERNAME.APPLICATIONS t \
            )'
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        applications = {}
        for applicationName, tasksWithDependencyStr, entryTasksInJson in \
                result:
            tasksWithDependency = {}
            tasksWithDependencyStr = tasksWithDependencyStr.read()
            entryTasksInJson = entryTasksInJson.read()
            for taskName, taskWithDependencyIndict \
                    in loads(tasksWithDependencyStr).items():
                parents = set([Task(name) for name in
                               taskWithDependencyIndict['parents']])
                children = set([Task(name) for name in
                                taskWithDependencyIndict['children']])
                taskWithDependency = TaskWithDependency(
                    name=taskName,
                    parents=parents,
                    children=children)
                tasksWithDependency[taskName] = taskWithDependency
            entryTasks = []
            for taskName in loads(entryTasksInJson):
                entryTasks.append(tasksWithDependency[taskName])
            applications[applicationName] = Application(
                applicationName,
                tasksWithDependency,
                entryTasks=entryTasks)
        return applications

    def writeApplication(self, application: Application):
        """
        Save an application to database
        :param application: Application object
        :return: None
        """
        pass

```

## Support in Arguments

**Finally**, edit `containers/master/sources/utils/master/application/manager.py`

```Python
ffrom typing import Dict

from .base import Application
from .database.adb import OracleAutonomousDatabase
from .database.mysqlDB import MySQLDatabase
from .task.base import Task
from ..config import MySQLEnvironment

Applications = Dict[str, Application]
TaskDependencies = Dict[str, Task]


class ApplicationManager:

    def __init__(
            self,
            databaseType: str = 'MariaDB'):
        """
        Initialize application manager with requires database
        :param databaseType: the database type
        """
        if databaseType == 'MariaDB':
            self.database = MySQLDatabase(
                user=MySQLEnvironment.user,
                password=MySQLEnvironment.password,
                host=MySQLEnvironment.host,
                port=MySQLEnvironment.port)
        elif databaseType == 'OracleAutonomousDatabase':
            # Oracle Autonomous Database is supported here as an argument
            self.database = OracleAutonomousDatabase()
        else:
            raise 'DatabaseType not support: ' + databaseType
        self.tasks: TaskDependencies = self.database.readTasks()
        self.applications: Applications = self.database.readApplications()

    def load(self):
        self.applications = self.database.readApplications()
        self.tasks = self.database.readTasks()

```

**Finally**, you can use it with argument `python3.9 master.py --databaseType OracleAutonomousDatabase`.


***Note:*** this guide only add support for `Applications` and `Tasks` databases. If you want to support others, edit `containers/master/sources/utils/master/logger/database/mysqlDB.py` and follow the steps above to support you new databases.