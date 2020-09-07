from copy import deepcopy
from pathlib import Path
from unittest import mock

import pytest

from server_manager.src.exceptions import InvalidFileError
from server_manager.src.files import (
    AdvancementsFile,
    File,
    MetaFile,
    PlayerDataFile,
    StatsFile,
)


@pytest.fixture(scope="class", autouse=True)
def reset_file_metaclass_attrs():
    for key in File.memory:
        File.memory[key] = []

    memory = File.memory.copy()
    subtypes = File.subtypes.copy()

    yield

    File.memory = memory
    File.subtypes = subtypes


class TestMetaFile:
    def test_work(self):
        # Meta.__init__ (declaring base class)
        class Base(metaclass=MetaFile):  # pylint: disable=R0903
            def __init__(self, number):
                self.number = number

            def __repr__(self):
                return f"{self.__class__.__name__}({self.number!r})"

        assert hasattr(Base, "memory")
        assert hasattr(Base, "subtypes")

        class Child1(Base):
            pass

        class Child2(Base):
            pass

        assert Base.memory == {"child1": [], "child2": []}
        assert Base.subtypes == {"child1": Child1, "child2": Child2}

        # Meta.__call__ (instantiating child classes)
        c11 = Child1(11)
        c12 = Child1(12)
        c13 = Child1(13)
        c21 = Child2(21)
        c22 = Child2(22)

        assert Base.memory == {"child1": [c11, c12, c13], "child2": [c21, c22]}
        assert Base.subtypes == {"child1": Child1, "child2": Child2}

        assert repr(c11) == "Child1(11)"
        assert repr(c12) == "Child1(12)"
        assert repr(c13) == "Child1(13)"
        assert repr(c21) == "Child2(21)"
        assert repr(c22) == "Child2(22)"

        # Some mix
        class Child3(Base):
            pass

        c31 = Child3(31)
        assert Base.memory == {
            "child1": [c11, c12, c13],
            "child2": [c21, c22],
            "child3": [c31],
        }
        assert Base.subtypes == {"child1": Child1, "child2": Child2, "child3": Child3}


class TestFile:
    @classmethod
    def setup_class(cls):
        class TypeA(File):
            pass

        class TypeB(File):
            pass

        class TypeC(File):
            pass

        cls.subtypes = {"typea": TypeA, "typeb": TypeB, "typec": TypeC}
        cls.memory = {"typea": [], "typeb": [], "typec": []}

        cls.TypeA = TypeA
        cls.TypeB = TypeB
        cls.TypeC = TypeC

    @pytest.fixture(autouse=True)
    def reset_memory(self):
        File.subtypes = deepcopy(self.subtypes)
        File.memory = deepcopy(self.memory)
        yield

    @pytest.fixture
    def file_creator(self):
        def wrapped(path):
            file = object.__new__(File)
            file.__init__(path=path)
            return file

        yield wrapped

    def test_uuid_pattern(self):
        test = File.uuid_pattern.search

        assert test("00000000-0000-0000-0000-000000000000.dat")
        assert test("550e8400-e29b-41d4-a716-446655440000.dat")
        assert test("00000000-0000-0000-C000-000000000046.dat")
        assert test("01234567-89ab-cdef-0123-456789abcdef.dat")
        assert not test("01234567-89ab-cdef-0123-456789abcdef.dat_old")
        assert not test("xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx")
        assert not test("invalid-uuid")

    def test_init(self):
        # pylint: disable=invalid-name
        # Not identified
        test_file = File("path")
        assert test_file is None
        assert File.memory == {"typea": [], "typeb": [], "typec": []}

        # Identify TypeA file
        f1 = File("/world/typea/00000000-0000-0000-0000-000000000000.json")
        assert isinstance(f1, self.TypeA)
        assert File.memory == {"typea": [f1], "typeb": [], "typec": []}

        # Identify TypeB file
        f2 = File("/world/typeb/00000000-0000-0000-0000-000000000000.json")
        assert isinstance(f2, self.TypeB)
        assert File.memory == {"typea": [f1], "typeb": [f2], "typec": []}

        # Identify TypeC file
        f3 = File("/world/typec/00000000-0000-0000-0000-000000000000.json")
        assert isinstance(f3, self.TypeC)
        assert File.memory == {"typea": [f1], "typeb": [f2], "typec": [f3]}

        # Identify another TypeA file
        f4 = File("/world/typea/01234567-89ab-cdef-0123-456789abcdef.json")
        assert isinstance(f1, self.TypeA)
        assert File.memory == {"typea": [f1, f4], "typeb": [f2], "typec": [f3]}

    def test_attributes(self, file_creator):
        # Build object manually
        test_file = file_creator("path")

        assert hasattr(test_file, "path")
        assert test_file.path == Path("path")

        assert vars(test_file) == {"path": Path("path")}

    def test_uuid(self, file_creator):
        def test(path):
            return file_creator(path).uuid

        def not_uuid(path):
            with pytest.raises(InvalidFileError):
                assert file_creator(path).uuid
            return True

        assert test("path/file-00000000-0000-0000-0000-000000000000.json")
        assert test("path/file-550e8400-e29b-41d4-a716-446655440000.dat")
        assert test("path/file-00000000-0000-0000-C000-000000000046.xml")

        assert not_uuid("/var/invalid/xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx.invalid")
        assert not_uuid("/home/user/test/invalid-uuid.png")

    def test_get_uuid_from_filepath(self):
        test = File.get_uuid_from_filepath
        assert test("path/file-00000000-0000-0000-0000-000000000000.json")
        assert test("path/file-550e8400-e29b-41d4-a716-446655440000.dat")
        assert not test("path/file-550e8400-e29b-41d4-a716-446655440000.dat_old")
        assert test("path/file-00000000-0000-0000-C000-000000000046.xml")

        assert not test("/var/invalid/xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx.invalid")
        assert not test("/home/user/test/invalid-uuid.png")

    @mock.patch("pathlib.Path.read_bytes")
    def test_read_bytes(self, read_m, file_creator):
        read_m.return_value = b"binary data"
        file = file_creator("/path/to/file.ext")

        assert file.read_bytes() == b"binary data"
        read_m.assert_called_once_with()

    @mock.patch("pathlib.Path.unlink")
    def test_remove(self, unlink_m, file_creator):
        file = file_creator("/path/to/file.ext")
        file.remove()
        unlink_m.assert_called_once_with()

    def test_as_posix(self, file_creator):
        file = file_creator("/path/to/file.ext")
        assert file.as_posix() == "/path/to/file.ext"

    @mock.patch("pathlib.Path.rename")
    def test_change_uuid(self, rename_m, file_creator, caplog):
        caplog.set_level(10, "server_manager.src.files")

        file: File = file_creator("file_type/00000000-0000-0000-C000-000000000046.json")
        new_uuid = "550e8400-e29b-41d4-a716-446655440000"
        file.change_uuid(new_uuid)

        expected_path = Path("file_type/550e8400-e29b-41d4-a716-446655440000.json")
        rename_m.assert_called_with(expected_path)

        assert len(caplog.records) == 1
        assert caplog.records[-1].levelname == "DEBUG"

        # In this case, 'foo' shouldn't be there, so File.change_uuid will remove it.
        file = file_creator("file_type/foo-00000000-0000-0000-C000-000000000046.json")
        new_uuid = "550e8400-e29b-41d4-a716-446655440000"
        file.change_uuid(new_uuid)

        expected_path = Path("file_type/550e8400-e29b-41d4-a716-446655440000.json")
        rename_m.assert_called_with(expected_path)

        assert len(caplog.records) == 2
        assert caplog.records[-1].levelname == "DEBUG"

    def test_identify(self):
        assert File.memory == self.memory
        assert File.subtypes == self.subtypes

        file_a1 = File.identify("/file/typea/1")
        file_a2 = File.identify("/file/typea/2")
        file_a3 = File.identify("/file/typea/3")
        file_b1 = File.identify("/file/typeb/1")
        file_b2 = File.identify("/file/typeb/2")
        file_c1 = File.identify("/file/typec/1")
        invalid = File.identify("invalid")

        assert isinstance(file_a1, self.TypeA)
        assert file_a1.path == Path("/file/typea/1")

        assert isinstance(file_a2, self.TypeA)
        assert file_a2.path == Path("/file/typea/2")

        assert isinstance(file_a3, self.TypeA)
        assert file_a3.path == Path("/file/typea/3")

        assert isinstance(file_b1, self.TypeB)
        assert file_b1.path == Path("/file/typeb/1")

        assert isinstance(file_b2, self.TypeB)
        assert file_b2.path == Path("/file/typeb/2")

        assert isinstance(file_c1, self.TypeC)
        assert file_c1.path == Path("/file/typec/1")

        assert invalid is None
        assert File.memory == {
            "typea": [file_a1, file_a2, file_a3],
            "typeb": [file_b1, file_b2],
            "typec": [file_c1],
        }

    def test_identify_2(self):
        assert File.memory == self.memory
        assert File.subtypes == self.subtypes

        # Not identified
        test_file = File.identify("path")
        assert test_file is None
        assert File.memory == {"typea": [], "typeb": [], "typec": []}

        # Identify TypeA file
        file1 = File.identify("/world/typea/00000000-0000-0000-0000-000000000000.json")
        assert isinstance(file1, self.TypeA)
        assert File.memory == {"typea": [file1], "typeb": [], "typec": []}

        # Identify TypeB file
        file2 = File.identify("/world/typeb/00000000-0000-0000-0000-000000000000.json")
        assert isinstance(file2, self.TypeB)
        assert File.memory == {"typea": [file1], "typeb": [file2], "typec": []}

        # Identify TypeC file
        file3 = File.identify("/world/typec/00000000-0000-0000-0000-000000000000.json")
        assert isinstance(file3, self.TypeC)
        assert File.memory == {"typea": [file1], "typeb": [file2], "typec": [file3]}

        # Identify another TypeA file
        file4 = File.identify("/world/typea/01234567-89ab-cdef-0123-456789abcdef.json")
        assert isinstance(file1, self.TypeA)
        assert File.memory == {
            "typea": [file1, file4],
            "typeb": [file2],
            "typec": [file3],
        }

    @mock.patch("os.walk")
    def test_gen_files(self, walk_m):
        def exp(string):
            return "00000000-0000-0000-0000-0000000000" + string

        walk = (
            ("./", ["typea", "typeb", "typec", "hidden"], []),
            ("./typea", [], [exp("a1.json"), exp("a2.json"), exp("a3.json")]),
            ("./typeb", [], [exp("b1.json"), exp("b2.json")]),
            ("./hidden", ["typec", "invalid-type", exp("c0.dat_old")], []),
            ("./hidden/invalid-type", [], ["a.pdf", "b.pdf", "c.pdf"]),
            ("./hidden/typec", [], [exp("c1.json")]),
        )

        walk_m.return_value = walk
        files = File.gen_files(Path("./"))

        assert files is None
        typea = File.memory["typea"]
        typeb = File.memory["typeb"]
        typec = File.memory["typec"]

        assert len(typea) == 3
        assert len(typeb) == 2
        assert len(typec) == 1

        assert typea[0].path == Path("typea/00000000-0000-0000-0000-0000000000a1.json")
        assert typea[1].path == Path("typea/00000000-0000-0000-0000-0000000000a2.json")
        assert typea[2].path == Path("typea/00000000-0000-0000-0000-0000000000a3.json")

        assert typeb[0].path == Path("typeb/00000000-0000-0000-0000-0000000000b1.json")
        assert typeb[1].path == Path("typeb/00000000-0000-0000-0000-0000000000b2.json")

        assert typec[0].path == Path(
            "hidden/typec/00000000-0000-0000-0000-0000000000c1.json"
        )

    def test_repr(self, file_creator):
        file = file_creator("/path/to/file.ext")
        assert repr(file) == "File('/path/to/file.ext')"

        class SubFile(File):
            pass

        path2 = "/world/subfile/00000000-0000-0000-0000-000000000000.json"
        a_file = SubFile(path2)
        assert repr(a_file) == f"SubFile('{path2}')"


class TestPlayerDataFile:
    def test_inheritance(self):
        player_data_file = PlayerDataFile("path")
        assert isinstance(player_data_file, PlayerDataFile)
        assert isinstance(player_data_file, File)


class TestStatsFile:
    def test_inheritance(self):
        stats_file = StatsFile("path")
        assert isinstance(stats_file, StatsFile)
        assert isinstance(stats_file, File)


class TestAdvancementsFile:
    def test_inheritance(self):
        advancements_file = AdvancementsFile("path")
        assert isinstance(advancements_file, AdvancementsFile)
        assert isinstance(advancements_file, File)
