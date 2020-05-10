import base64
from io import StringIO

import pandas as pd
import pyperclip

BASE64_DF = (
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

_DF = pd.read_csv(
    StringIO(base64.b64decode(BASE64_DF.encode()).decode()), index_col="uuid"
)


def get_uuid(username, mode):
    mask = (_DF.username == username) & (_DF.online == mode)
    return _DF[mask].iloc[0].name


def get_username(uuid):
    return _DF.loc[uuid, "username"]


def get_mode(uuid):
    return _DF.loc[uuid, "online"]


def get_dataframe() -> pd.DataFrame:
    return _DF.copy()


def excel_to_b64(excel_path: str):
    df = pd.read_excel("players-data.xlsx")
    df.set_index("uuid", inplace=True)

    bytes_df = df.to_csv(index="uuid").encode()

    b64data = base64.b64encode(bytes_df).decode()
    print(b64data)
    pyperclip.copy(b64data)
