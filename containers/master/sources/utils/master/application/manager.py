from typing import Dict

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
            raise 'DatabaseType not supported: ' + databaseType
        self.tasks: TaskDependencies = self.database.readTasks()
        self.applications: Applications = self.database.readApplications()

    def load(self):
        self.applications = self.database.readApplications()
        self.tasks = self.database.readTasks()
