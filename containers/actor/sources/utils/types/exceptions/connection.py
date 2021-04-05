class CannotBindAddr(Exception):

    def __init__(self):
        super(CannotBindAddr, self).__init__('can not bind address')
