class NoWorkerAvailableException(Exception):

    def __init__(self):
        super(NoWorkerAvailableException, self).__init__('No Worker Available')


class ClientDisconnected(Exception):

    def __init__(self):
        super(ClientDisconnected, self).__init__('Client Disconnected')


class WorkerCredentialNotValid(Exception):

    def __init__(self):
        super(WorkerCredentialNotValid, self).__init__('Worker Credential is Not Valid')


class MessageDoesNotContainRespondAddr(Exception):

    def __init__(self):
        super(MessageDoesNotContainRespondAddr, self).__init__('Message does not contain responding address')


class RegisteredAsWrongRole(Exception):

    def __init__(self):
        super(RegisteredAsWrongRole, self).__init__('Registered As Wrong Role')
