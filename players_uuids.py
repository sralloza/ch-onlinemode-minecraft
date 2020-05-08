import base64
import json
import sys
from dataclasses import dataclass, field
from io import StringIO
from itertools import groupby
from json import JSONDecodeError
from pathlib import Path
from uuid import UUID

import pandas as pd
import requests


@dataclass
class Player:
    uuid: str = field(repr=False)
    username: str
    online: bool

    def __bool__(self):
        return bool(self.username)

    def to_json(self):
        return self.__dict__.copy()


b64_data = (
    "dXVpZCx1c2VybmFtZSxvbmxpbmUNCjQ1MzBkMTNjLWM4ZjMtNDM1MC05YzJkLTM5Mm"
    "FhNTNmMTVlMSxsdXNpY3JhZnQsVHJ1ZQ0KMGM5M2E2NjktODdjZi0zYTZkLTk5Y2Ut"
    "MzI3NTVjMTA1ODdlLGx1c2ljcmFmdCxGYWxzZQ0KNGE2MTg3NjgtNGYyNi00Njg4LT"
    "hhYjUtNmU2NGYyNTBjNjJmLFNyQWxsb3phLFRydWUNCmJlMTc2NDBiLTg0NzEtMzIx"
    "ZS1hMzU1LWQyYTI4NTllYmRhMSxTckFsbG96YSxGYWxzZQ0KYTE5YzI4NDAtY2ZhZS"
    "00OGMxLTk5ZGMtMzQ5MjQ0NDZiMGY0LE1JQ0hBRUxDUkFGNyxUcnVlDQpkNTljMTI4"
    "NS05NDNhLTM0MjItODRiZC0wYjdhZDE2ZTM1YjUsTUlDSEFFTENSQUY3LEZhbHNlDQ"
    "oxMjhhMDliNi1mOGVlLTQyZTItYTdkYy0xZDEyOWYxNGYwZDksQmFidWNoYXMsVHJ1"
    "ZQ0KYjFmYzRmNWMtMDA4Mi0zNjU4LWJiYzgtZjViMWY3YzlmZTBjLEJhYnVjaGFzLE"
    "ZhbHNlDQo3NTU2NWViOC0zYTYxLTRlNzctYmUxOC04MDJjYmFkMGZmMDMsR2FsZXNh"
    "aXpfOTgsVHJ1ZQ0KMDM0YTU1OGEtOGVjYS0zOTZiLWE4ODMtM2Q3OWE5NTZlNDcxLE"
    "dhbGVzYWl6Xzk4LEZhbHNlDQphOTczNWY2Ni1mNzc5LTQ0ZTMtOTc0ZS04MTRkN2Rh"
    "MGU1NGYsVGFua3J1czk4LFRydWUNCjFjMTFlN2IxLWEzZjAtMzRmNy1hOWVlLTBiMj"
    "gzNmE1M2FkMixUYW5rcnVzOTgsRmFsc2UNCjMwOGZjZDI3LTQ5YTgtNDc5NS1hNmEw"
    "LTU2OGVlZjBjYTk2NCxBeGVoOTksVHJ1ZQ0KZWEwYmZjMTItZTI0ZC0zYmI2LTliNG"
    "YtMDhkN2M0NTc2M2UwLEF4ZWg5OSxGYWxzZQ0K"
)

df = pd.read_csv(
    StringIO(base64.b64decode(b64_data.encode()).decode()), index_col="uuid"
)


def uuid_to_player(uuid):
    try:
        data = df.loc[uuid, ["username", "online"]]
        return Player(uuid, data.username, data.online)
    except KeyError:
        print(f"ERROR: {uuid}", file=sys.stderr)
        return Player(uuid, None, None)
