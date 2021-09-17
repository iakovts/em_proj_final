#from distutils.core import setup
from setuptools import find_packages, setup

reqs = ["numpy", "fdtd"]

setup(
    name="micwave",
    version="1.0",
    description="Methods and solutions Microwave Oven simulation",
    author="Iakovos Tsouros",
#    package_dir={"scripts": "src", "common": "src"},
    packages=find_packages(include=["src*", "util*"]),
    python_requires=">3.6.*",
    install_requires=reqs
)
