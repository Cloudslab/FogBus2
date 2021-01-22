class NoWorkerAvailableException(Exception):

    def __init__(self):
        super(NoWorkerAvailableException, self).__init__('No Worker Available')


class ClientDisconnected(Exception):

    def __init__(self):
        super(ClientDisconnected, self).__init__('Client Disconnected')


class WorkerCredentialNotValid(Exception):

    def __init__(self):
        super(WorkerCredentialNotValid, self).__init__('Worker Credential is Not Valid')


class MessageDoesNotContainSourceInfo(Exception):

    def __init__(self):
        super(MessageDoesNotContainSourceInfo, self).__init__('Message does not contain source information')


class MessageDoesNotContainType(Exception):

    def __init__(self):
        super(MessageDoesNotContainType, self).__init__('Message does not contain Type')


class RegisteredAsWrongRole(Exception):

    def __init__(self):
        super(RegisteredAsWrongRole, self).__init__('Registered As Wrong Role')


class CannotBindAddr(Exception):

    def __init__(self):
        super(CannotBindAddr, self).__init__('can not bind address')
