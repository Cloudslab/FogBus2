import unittest
from unittest import TestCase

from .base import Application
from .mysqlDB import ADB
from ..task.base import Task


class MyTestCase(TestCase):
    db = ADB()

    def testReadTasks(self):
        tasks = self.db.readTasks()
        if not len(tasks):
            self.assertTrue(True)
            return
        if isinstance(list(tasks.values())[0], Task):
            self.assertTrue(True)
            return

    def testWriteTask(self):
        taskName = 'TEST_TASK_NAME'
        self.db.writeTask(taskName)
        self.assertTrue(True)

    def testReadApplications(self):
        applications = self.db.readApplications()
        if not len(applications):
            self.assertTrue(True)
            return
        if isinstance(list(applications.values())[0], Application):
            self.assertTrue(True)
            return

    def testWriteApplication(self):
        pass


if __name__ == '__main__':
    unittest.main()
