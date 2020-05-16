class ServerManagerError(Exception):
    pass


class InvalidServerStateError(ServerManagerError):
    pass


class InvalidPlayerDataStateError(ServerManagerError):
    pass
