from pathlib import Path

from setuptools import find_packages, setup

import versioneer

requirements = Path(__file__).with_name("requirements.txt").read_text().splitlines()

setup(
    name="lia",
    version=versioneer.get_version(),
    entry_points={"console_scripts": ["lia=server_manager.main:main"]},
    packages=find_packages(),
    install_requires=requirements,
    cmdclass=versioneer.get_cmdclass(),
    include_package_data=True,
)
