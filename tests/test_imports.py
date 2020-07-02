def test_import_pandas():
    import pandas as pd

    assert pd


def test_import_colorama():
    from colorama import Fore

    assert Fore


def test_import_nbtlib():
    from nbtlib import File

    assert File


def test_import_numpy():
    import numpy as np

    assert np


def test_import_pyperclip():
    from pyperclip import copy, paste

    assert copy
    assert paste


def test_import_requests():
    import requests

    assert requests


def test_import_xlrd():
    import xlrd

    assert xlrd
