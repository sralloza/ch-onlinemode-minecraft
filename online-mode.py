import argparse
import re
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("server.properties")
pattern: re.Pattern = re.compile(r"(online-mode=)(\w+)", re.IGNORECASE)


class Memory:
    parser = None


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def bool2str(b):
    return str(b).lower()


def parse_args() -> dict:
    parser = argparse.ArgumentParser("online-mode-manager")
    parser.add_argument("online-mode", type=str2bool, nargs="?")
    Memory.parser = parser
    return vars(parser.parse_args())


def update_config(online_mode=None):
    file_data = CONFIG_PATH.read_text(encoding="utf-8")
    current_online_mode = str2bool(pattern.search(file_data).group(2))

    if online_mode is None:
        print(f"online-mode is set to {current_online_mode}")
        sys.exit()

    if online_mode == current_online_mode:
        Memory.parser.error(f"online-mode is already set to {current_online_mode}")
        sys.exit()

    changed_file_data = pattern.sub(r"\1" + bool2str(online_mode), file_data)
    CONFIG_PATH.write_text(changed_file_data, encoding="utf-8")


def main():
    args = parse_args()
    online_mode = args["online-mode"]
    update_config(online_mode=online_mode)
    print(f"Set online-mode to {online_mode}")


if __name__ == "__main__":
    main()
