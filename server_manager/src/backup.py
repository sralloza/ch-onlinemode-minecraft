from datetime import datetime
import logging
from os import makedirs
from platform import system
from subprocess import DEVNULL, PIPE, run

from .exceptions import SFKError, SFKNotFoundError
from .paths import get_server_path


def is_sfk_installed():
    if system() == "Windows":
        args = ["where", "sfk"]
    else:
        args = ["which", "sfk"]

    command = run(args, stdin=DEVNULL,stderr=DEVNULL, stdout=DEVNULL)
    return command.returncode == 0


def get_backups_folder():
    backups_folder = get_server_path().with_name("backups")
    makedirs(backups_folder, exist_ok=True)
    return backups_folder


def get_backup_zipfile_path():
    timestamp = datetime.now().strftime("%Y.%m.%d.%H.%M")
    return get_backups_folder().joinpath(f"LIA-backup-{timestamp}.zip")


def run_sfk():
    logger = logging.getLogger(__name__)
    server_path = get_server_path()
    backup_zipfile_path = get_backup_zipfile_path()

    logger.debug(
        "Creating backup of %r to %r",
        server_path.as_posix(),
        backup_zipfile_path.as_posix(),
    )

    command = run(
        ["sfk", "zip", backup_zipfile_path.as_posix(), server_path.as_posix(), "-yes"],
        stdin=DEVNULL,
        stdout=PIPE,
        stderr=PIPE,
    )

    if command.returncode != 0:
        logger.critical(
            "Error running SFK (stdout=%s, stderr=%s)", command.stdout, command.stderr
        )
        raise SFKError("Error running SFK")


def create_backup():
    if not is_sfk_installed():
        raise SFKNotFoundError("SFK is not installed or is not in the PATH")

    run_sfk()
