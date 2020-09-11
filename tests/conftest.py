from pathlib import Path
import os

TEST_PATH = Path(__file__).parent.parent.joinpath(
    "server_manager/src/data/server-path.testing"
)


def pytest_configure():
    os.environ["TESTING"] = "True"
    os.environ["SERVER-PATH-TESTING"] = TEST_PATH.as_posix()
    server_path = "/path/to/server"
    os.makedirs(TEST_PATH.parent, exist_ok=True)
    TEST_PATH.write_text(server_path)


def pytest_unconfigure():
    TEST_PATH.unlink()
