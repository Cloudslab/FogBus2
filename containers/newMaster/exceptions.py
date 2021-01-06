class NoWorkerAvailableException(Exception):

    def __init__(self):
        super(NoWorkerAvailableException, self).__init__('No Worker Available')


class ClientDisconnected(Exception):

    def __init__(self):
        super(ClientDisconnected, self).__init__('Client Disconnected')


class WorkerCredentialNotValid(Exception):

    def __init__(self):
        super(WorkerCredentialNotValid, self).__init__('Worker Credential is Not Valid')