from abc import abstractmethod
from json import loads
from typing import Dict

from mysql import connector

from .base import BaseDatabase
from ..base import Application
from ..task.base import Task
from ..task.dependency.base import TaskWithDependency


class MySQLDatabase(BaseDatabase):

    def __init__(
            self,
            user: str = 'root',
            password: str = 'passwordForRoot',
            host: str = '127.0.0.1',
            port: int = 3306,
            dbTasks: str = 'FogBus2_Tasks',
            dbApplications: str = 'FogBus2_Applications',
            **kwargs):
        BaseDatabase.__init__(self)
        self.dbTasks = connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbTasks,
            **kwargs)

        self.dbApplications = connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbApplications,
            **kwargs)

        self.cursorTask = self.dbTasks.cursor()
        self.cursorApplication = self.dbApplications.cursor()

    def readTasks(self) -> Dict[str, Task]:
        sql = 'SELECT * ' \
              'FROM tasks'
        self.cursorTask.execute(sql)
        result = self.cursorTask.fetchall()
        tasks = {}
        for taskName in result:
            tasks[taskName] = Task(taskName)
        return tasks

    @abstractmethod
    def writeTask(self, taskName: str):
        sql = 'INSERT INTO tasks' \
              ' (name) ' \
              'VALUES("%s")' % taskName
        self.cursorTask.execute(sql)
        self.dbTasks.commit()

    @abstractmethod
    def readApplications(self) -> Dict[str, Application]:
        sql = 'SELECT * ' \
              'FROM applications'
        self.cursorApplication.execute(sql)
        result = self.cursorApplication.fetchall()
        applications = {}
        for _, applicationName, tasksWithDependencyStr, entryTasksInJson, _ in \
                result:
            tasksWithDependency = {}
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
        pass
