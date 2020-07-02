from pathlib import Path

from setuptools import find_packages, setup

import versioneer

requirements = Path(__file__).with_name("requirements.txt").read_text().splitlines()

setup(
    name="server-manager",
    version=versioneer.get_version(),
    packages=find_packages(),
    install_requires=requirements,
    cmdclass=versioneer.get_cmdclass(),
)
