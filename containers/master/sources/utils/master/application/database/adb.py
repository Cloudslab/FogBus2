from json import loads
from typing import Dict

import cx_Oracle

from .base import BaseDatabase
from ..base import Application
from ..task.base import Task
from ..task.dependency.base import TaskWithDependency


class OracleAutonomousDatabase(BaseDatabase):

    def __init__(
            self,
            user: str = 'admin',
            password: str = '@Dibadiba1993',
            dsn: str = 'fogbus2_high',
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
                FROM ADMIN.TASKS t \
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
                FROM ADMIN.APPLICATIONS t \
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
