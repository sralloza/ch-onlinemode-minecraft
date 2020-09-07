"""Manages backups of the minecraft server."""

import logging
from datetime import datetime
from functools import lru_cache
from os import makedirs
from pathlib import Path
from platform import system
from subprocess import DEVNULL, PIPE, CalledProcessError, run

from .exceptions import SFKError, SFKNotFoundError
from .paths import get_server_path


def is_sfk_installed() -> bool:
    """Checks if the Swiss File Knife tool is in the PATH.

    Returns:
        bool: True for success, False otherwise.
    """

    if system() == "Windows":
        args = ["where", "sfk"]
    else:
        args = ["which", "sfk"]

    try:
        run(args, stdin=DEVNULL, stderr=DEVNULL, stdout=DEVNULL, check=True)
        return True
    except CalledProcessError:
        return False


@lru_cache(maxsize=10)
def get_backups_folder() -> Path:
    """Returns the folder where backups are stored.

    Returns:
        Path: backups folder.
    """

    backups_folder = get_server_path().with_name("backups")
    makedirs(backups_folder, exist_ok=True)
    return backups_folder


def get_backup_zipfile_path() -> Path:
    """Returns the backup zip filepath.

    Returns:
        Path: backup filepath.
    """

    timestamp = datetime.now().strftime("%Y.%m.%d.%H.%M")
    return get_backups_folder().joinpath(f"LIA-backup-{timestamp}.zip")


def run_sfk():
    """Runs SFK to zip the server folder.

    Raises:
        SFKError: if SFK doesn't return 0.
    """

    logger = logging.getLogger(__name__)
    server_path = get_server_path()
    backup_zipfile_path = get_backup_zipfile_path()

    logger.debug(
        "Creating backup of %r to %r",
        server_path.as_posix(),
        backup_zipfile_path.as_posix(),
    )

    try:
        run(
            [
                "sfk",
                "zip",
                backup_zipfile_path.as_posix(),
                server_path.as_posix(),
                "-yes",
            ],
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=PIPE,
            check=True,
        )
    except CalledProcessError as exc:
        logger.critical(
            "Error running SFK [%d] (stdout=%s, stderr=%s)",
            exc.returncode,
            exc.stdout,
            exc.stderr,
        )
        raise SFKError("Error running SFK") from exc

    logger.info("Backup created")


def create_backup():
    """Creates a backup of the minecraft server using the Swiss File Knife.

    Raises:
        SFKNotFoundError: if SFK is not found in the PATH.
    """

    if not is_sfk_installed():
        raise SFKNotFoundError("SFK is not installed or is not in the PATH")

    run_sfk()
