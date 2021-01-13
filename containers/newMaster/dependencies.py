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
    def __init__(self, name: str, dependencies: Dict[int, Dependency]):
        self.name: str = str(name)
        self.dependencies: Dict[int, Dependency] = dependencies


def loadDependencies():
    f = open('./dependencies.json')
    jsonData = json.loads(f.read())
    tasks: Dict[int, Task] = {}

    for taskID, taskData in jsonData['tasks'].items():
        task = Task(taskID=taskID, taskName=taskData['name'])
        tasks[taskID] = task

    applications: List[Application] = []

    for applicationID, applicationData in jsonData['applications'].items():
        dependenciesData = applicationData['dependencies']
        dependencies: Dict[int, Dependency] = {}
        for taskID, dependencyData in dependenciesData.items():
            dependency = Dependency(
                task=tasks[taskID],
                parentTasksList=dependencyData['parents'],
                childTaskList=dependencyData['children']
            )
            dependencies[taskID] = dependency

        application = Application(
            name=applicationData['name'],
            dependencies=dependencies
        )
        applications.append(application)
    return tasks, applications


if __name__ == '__main__':
    tasks_, applications_ = loadDependencies()
    print()
