# from distutils.core import setup
from setuptools import find_packages, setup

reqs = ["numpy", 'dataclasses;python_version<"3.7"']
extra_reqs = {"pres": ["plotly", "jupyterlab"]}
setup(
    name="micwave",
    version="1.0",
    description="Microwave Oven simulation",
    author="Iakovos Tsouros",
    packages=find_packages(include=["src*", "util*"]),
    python_requires=">3.6.*",
    install_requires=reqs,
    entry_points={
        "console_scripts": [
            "mic=micwave.src.main:run",
        ]
    },
    extras_require=extra_reqs,
)
