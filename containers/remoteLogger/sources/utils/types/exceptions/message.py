class MessageDoesNotContainSourceInfo(Exception):

    def __init__(self):
        super(MessageDoesNotContainSourceInfo, self).__init__(
            'Message does not contain source information')


class MessageDoesNotContainType(Exception):

    def __init__(self):
        super(MessageDoesNotContainType, self).__init__(
            'Message does not contain Type')
