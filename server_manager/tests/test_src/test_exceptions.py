import pytest

from server_manager.src.exceptions import (
    InvalidFileError,
    InvalidPlayerDataStateError,
    InvalidServerStateError,
    ServerManagerError,
)


class TestServerManagerError:
    def test_inheritance(self):
        assert issubclass(ServerManagerError, Exception)

    def test_raises(self):
        with pytest.raises(ServerManagerError):
            raise ServerManagerError


class TestInvalidServerStateError:
    def test_inheritance(self):
        assert issubclass(InvalidServerStateError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(InvalidServerStateError):
            raise InvalidServerStateError


class TestInvalidPlayerDataStateError:
    def test_inheritance(self):
        assert issubclass(InvalidPlayerDataStateError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(InvalidPlayerDataStateError):
            raise InvalidPlayerDataStateError


class TestInvalidFileError:
    def test_inheritance(self):
        assert issubclass(InvalidFileError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(InvalidFileError):
            raise InvalidFileError
