from argparse import ArgumentTypeError

import pytest

from server_manager.src.utils import bool2str, str2bool


def test_bool_to_str():
    assert bool2str(True) == "true"
    assert bool2str(False) == "false"


def test_str_to_bool_ok():
    assert str2bool(True) is True
    assert str2bool("true") is True
    assert str2bool("True") is True
    assert str2bool("TrUe") is True
    assert str2bool("TRUE") is True
    assert str2bool("t") is True
    assert str2bool("T") is True
    assert str2bool("yes") is True
    assert str2bool("y") is True
    assert str2bool("YeS") is True
    assert str2bool("Sí") is True
    assert str2bool("sí") is True
    assert str2bool("SI") is True
    assert str2bool("si") is True
    assert str2bool("1") is True
    assert str2bool(1) is True

    assert str2bool(False) is False
    assert str2bool("false") is False
    assert str2bool("False") is False
    assert str2bool("FalSE") is False
    assert str2bool("FALSE") is False
    assert str2bool("F") is False
    assert str2bool("f") is False
    assert str2bool("no") is False
    assert str2bool("No") is False
    assert str2bool("nO") is False
    assert str2bool("NO") is False
    assert str2bool("0") is False
    assert str2bool(0) is False


@pytest.mark.parametrize("mode", ["argparse", "normal"])
def test_str_to_bool_fail(mode):
    def test(string):
        string = str(string)
        if mode == "argparse":
            exc = ArgumentTypeError
            msg = "Boolean value expected"
            parser = True
        else:
            exc = ValueError
            msg = "%r is not a valid boolean" % string
            parser = False

        with pytest.raises(exc, match=msg):
            str2bool(string, parser=parser)

    test("invalid")
    test("hello there")
    test(654)
    test("True-")
    test("-False")
