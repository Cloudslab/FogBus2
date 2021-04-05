class Task:

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return 'Task(name=%s)' % self.name
