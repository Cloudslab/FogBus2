import json
from typing import List, Dict


class Task:
    def __init__(self, taskID: int, taskName: str):
        self.id: int = int(taskID)
        self.name: str = str(taskName)


class Dependency:

    def __init__(self, task: Task, parentTasksList: List = None, childTaskList: List = None):
        self.task: Task = task
        if parentTasksList is None:
            parentTasksList = []
        if childTaskList is None:
            childTaskList = []
        self.parentTasksList: List = parentTasksList
        self.childTaskList: List = childTaskList


class Application:
    def __init__(self, name: str, dependencies: Dict[str, Dependency]):
        self.name: str = str(name)
        self.dependencies: Dict[str, Dependency] = dependencies


def loadDependencies():
    f = open('dependencies.json')
    jsonData = json.loads(f.read())
    tasks: Dict[str, Task] = {}

    for taskName, taskData in jsonData['tasks'].items():
        task = Task(taskID=taskData['id'], taskName=taskName)
        tasks[taskName] = task

    applications: Dict[str, Application] = {}

    for applicationID, applicationData in jsonData['applications'].items():
        dependenciesData = applicationData['dependencies']
        dependencies: Dict[str, Dependency] = {}
        for taskName, dependencyData in dependenciesData.items():
            dependency = Dependency(
                task=tasks[taskName],
                parentTasksList=dependencyData['parents'],
                childTaskList=dependencyData['children']
            )
            dependencies[taskName] = dependency

        application = Application(
            name=applicationData['name'],
            dependencies=dependencies
        )
        applications[application.name] = application
    return tasks, applications


if __name__ == '__main__':
    tasks_, applications_ = loadDependencies()
    print()
