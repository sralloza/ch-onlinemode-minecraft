import pytest

from server_manager.src.dataframe import _DF as df
from server_manager.src.dataframe import get_dataframe, get_mode, get_username, get_uuid


def test_dataframe():
    for username, group in df.groupby("username"):
        assert len(group) == 2
        first = group.iloc[0]
        second = group.iloc[1]

        assert first.name != second.name
        assert first.username == second.username == username
        assert first.online != second.online
        assert first.online == (not second.online)

    assert df.index.name == "uuid"
    assert list(df.columns) == ["username", "online"]


def test_get_uuid():
    assert get_uuid("SrAlloza", True) == "4a618768-4f26-4688-8ab5-6e64f250c62f"
    assert get_uuid("SrAlloza", False) == "be17640b-8471-321e-a355-d2a2859ebda1"


def test_get_username():
    assert get_username("4a618768-4f26-4688-8ab5-6e64f250c62f") == "SrAlloza"
    assert get_username("be17640b-8471-321e-a355-d2a2859ebda1") == "SrAlloza"


def test_get_mode():
    assert get_mode("4a618768-4f26-4688-8ab5-6e64f250c62f") is True
    assert get_mode("be17640b-8471-321e-a355-d2a2859ebda1") is False


def test_get_dataframe():
    df2 = get_dataframe()
    assert df2.equals(df)
    assert df2 is not df


@pytest.mark.skip
def test_excel_to_b64():
    assert 0
