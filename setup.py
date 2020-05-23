from pathlib import Path

from setuptools import find_packages, setup

requirements = Path(__file__).with_name("requirements.txt").read_text().splitlines()

setup(
    name="server-manager",
    version="1.0",
    packages=find_packages(),
    install_requires=requirements,
)
