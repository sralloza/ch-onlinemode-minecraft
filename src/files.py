import os
import re
from collections import defaultdict
from pathlib import Path


class MetaFile(type):
    def __init__(cls, name, bases, attrs, **kwargs):
        type.__init__(cls, name, bases, attrs, **kwargs)

        if not bases:
            cls._subtypes = {}
            cls.memory = {}
        else:
            bases[0]._subtypes[name.lower().replace("file", "")] = cls
            bases[0].memory[name.lower().replace("file", "")] = list()

        # print(cls, name, bases, attrs, **kwargs)

    def __call__(cls, *args, **kwargs):
        instance = type.__call__(cls, *args, **kwargs)
        classname = cls.__name__.lower().replace("file", "")
        cls.__bases__[0].memory[classname].append(instance)
        return instance


class File(metaclass=MetaFile):
    uuid_pattern = re.compile(
        r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}"
    )

    def __init__(self, path):
        self.path = Path(path)

    @property
    def uuid(self):
        return self.uuid_pattern.search(self.path.as_posix()).group()

    def as_posix(self):
        return self.path.as_posix()

    def change_uuid(self, uuid):
        old_uuid = self.uuid
        new_path = self.path.with_name(uuid + self.path.suffix)
        self.path.rename(new_path)
        self.path = new_path
        return True

    @classmethod
    def identify(cls, path):
        path = Path(path).as_posix()
        for subtype in cls._subtypes:
            if subtype in path:
                return cls._subtypes[subtype](path)
        assert 0

    @classmethod
    def gen_files(cls, path):
        for root, dirs, files in os.walk(path):
            for filename in files:
                file = Path(root).joinpath(filename)
                match = uuid_pattern.search(file.as_posix())
                if match:
                    File.identify(file)

    def __repr__(self):
        return f"{type(self).__name__}({self.path!r})"


class PlayerDataFile(File):
    pass


class StatsFile(File):
    pass


class AdvancementsFile(File):
    pass


if __name__ == "__main__":
    File.gen_files("D:/Sistema/Desktop/lia-backup/LIA 2020")
    for file_group in File.memory.values():
        for file in file_group:
            file.change_uuid("asdf-1234")
