import base64
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import pyperclip


def generate_b64_data():
    df = pd.read_excel("players-data.xlsx")
    df.set_index("uuid", inplace=True)


    bytes_df = df.to_csv(index="uuid").encode()

    b64data = base64.b64encode(bytes_df).decode()
    print(b64data)
    pyperclip.copy(b64data)


def parse_b64_data():
    b64data = pyperclip.paste()
    bytes_df = base64.b64decode(b64data.encode())
    # print(bytes_df)
    df = pd.read_csv(StringIO(bytes_df.decode()))
    print(df)


generate_b64_data()
