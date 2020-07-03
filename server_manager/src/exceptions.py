"""Exceptions used in `server_manager`."""


class ServerManagerError(Exception):
    """Server manager error."""


class InvalidFileError(ServerManagerError):
    """Invalid file error."""


class InvalidPlayerDataStateError(ServerManagerError):
    """Invalid player data state error."""


class InvalidPlayerError(ServerManagerError):
    """Invalid player error."""


class InvalidServerStateError(ServerManagerError):
    """Invalid server state error."""


class SearchError(ServerManagerError):
    """Search error."""
