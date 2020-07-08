import pytest

from server_manager.src.exceptions import (
    CheckError,
    InvalidFileError,
    InvalidPlayerDataStateError,
    InvalidPlayerError,
    InvalidPluginStateError,
    InvalidServerStateError,
    SFKNotFoundError,
    SearchError,
    ServerManagerError,
)


class TestServerManagerError:
    def test_inheritance(self):
        assert issubclass(ServerManagerError, Exception)

    def test_raises(self):
        with pytest.raises(ServerManagerError):
            raise ServerManagerError


class TestCheckError:
    def test_inheritance(self):
        assert issubclass(CheckError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(CheckError):
            raise CheckError


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


class TestInvalidPluginStateError:
    def test_inheritance(self):
        assert issubclass(InvalidPluginStateError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(InvalidPluginStateError):
            raise InvalidPluginStateError


class TestInvalidFileError:
    def test_inheritance(self):
        assert issubclass(InvalidFileError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(InvalidFileError):
            raise InvalidFileError


class TestSearchError:
    def test_inheritance(self):
        assert issubclass(SearchError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(SearchError):
            raise SearchError


class TestInvalidPlayerError:
    def test_inheritance(self):
        assert issubclass(InvalidPlayerError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(InvalidPlayerError):
            raise InvalidPlayerError


class TestSFKNotFoundError:
    def test_inheritance(self):
        assert issubclass(SFKNotFoundError, ServerManagerError)

    def test_raises(self):
        with pytest.raises(SFKNotFoundError):
            raise SFKNotFoundError
