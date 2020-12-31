class NoWorkerAvailableException(Exception):

    def __init__(self):
        super(NoWorkerAvailableException, self).__init__('No Worker Available')
