"""Exceptions used in `server_manager`."""


class ServerManagerError(Exception):
    """Server manager error."""


class InvalidServerStateError(ServerManagerError):
    """Invalid server state error."""


class InvalidPlayerDataStateError(ServerManagerError):
    """Invalid player data state error."""


class InvalidFileError(ServerManagerError):
    """Invalid file error."""


class InvalidPlayerError(ServerManagerError):
    """Invalid player error."""
