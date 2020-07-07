"""Exceptions used in `server_manager`."""


class ServerManagerError(Exception):
    """Server manager error."""


class CheckError(ServerManagerError):
    """Check error."""


class InvalidFileError(ServerManagerError):
    """Invalid file error."""


class InvalidPlayerDataStateError(ServerManagerError):
    """Invalid player data state error."""


class InvalidPlayerError(ServerManagerError):
    """Invalid player error."""


class InvalidPluginStateError(ServerManagerError):
    """Invalid plugin state error."""


class InvalidServerStateError(ServerManagerError):
    """Invalid server state error."""


class SearchError(ServerManagerError):
    """Search error."""
