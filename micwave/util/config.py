import numpy as np

from dataclasses import dataclass, field, make_dataclass
from typing import Tuple


FOODSTUFF_CFG = {
    915: {
        "potato1": {
            "er": 65,
            "sigma": 1.02,
        },
        "potato2": {
            "er": 65,
            "sigma": 1.02,
        },
        "burger": {
            "er": 55,
            "sigma": 0.95,
        },
        "plate": {
            "er": 6,
            "sigma": 0.001,
        },
    },
    2450: {
        "potato1": {
            "er": 54,
            "sigma": 2.18,
        },
        "potato2": {
            "er": 54,
            "sigma": 2.18,
        },
        "burger": {
            "er": 52,
            "sigma": 1.74,
        },
        "plate": {
            "er": 6,
            "sigma": 0.001,
        },
    },
}


@dataclass(eq=False)
class CavItem:
    er: int = 0
    sigma: float = 0
    freq: float = 0
    dens: float = field(default=1000)
    power: float = field(default=117)  # Source Power (V/m)


@dataclass(eq=False)
class DimensionsRect:
    # Boilerplate for dimensional objects (Rectangular)
    x: float
    y: float
    z: float


@dataclass(eq=False)
class DimensionsSpher:
    # Boilerplate for dimensional objects (Spherical)
    r: float
    z: float = field(default=None)
    center: Tuple = field(default=None)  # Initial coords


@dataclass(eq=False)
class DimBase:
    # All dimensions in m
    oven: DimensionsRect = field(default=DimensionsRect(x=0.17, y=0.17, z=0.15))
    source: DimensionsRect = field(default=DimensionsRect(x=0.046, y=0.092, z=0.049))
    burger: DimensionsSpher = field(default=DimensionsSpher(r=0.04, z=0.02))
    potato1: DimensionsSpher = field(default=DimensionsSpher(r=0.02))
    potato2: DimensionsSpher = field(default=DimensionsSpher(r=0.02))
    plate: DimensionsSpher = field(default=DimensionsSpher(r=0.07, z=0.01))

    def __post_init__(self):
        self.plate.center = (round(self.oven.x / 2, 4), round(self.oven.y / 2, 4))
        self.burger.center = (
            round(self.plate.center[0] - 0.025, 4),
            round(self.plate.center[1], 4),
        )
        self.potato1.center = (
            round(self.plate.center[0] + 0.035, 4),
            round(self.plate.center[1] + 0.025, 4),
        )
        self.potato2.center = (
            round(self.plate.center[0] + 0.035, 4),
            round(self.plate.center[1] - 0.025, 4),
        )


@dataclass(eq=False)
class Constants:
    # Constants
    c: float = 2.99792458e8  # Speed of light
    muz: float = 4.0 * np.pi * 1.0e-7  # permeability of free space
    epsz: float = field(init=False)  # permittivity of free space

    def __post_init__(self):
        self.epsz = 1.0 / (self.c * self.c * self.muz)


@dataclass(eq=False)
class Grid:
    # grid info
    spacing: float = 0.001


@dataclass
class CfgBase:
    f915: CavItem = field(init=False)
    f2450: CavItem = field(init=False)
    dims: DimBase = field(default=DimBase())
    const: Constants = field(default=Constants())
    grid: Grid = field(default=Grid())


def make_cfg():
    cfg = CfgBase()
    for freq, food in FOODSTUFF_CFG.items():
        foods_base = []
        for obj, val in food.items():
            food_tuple = (
                obj,
                CavItem,
                field(
                    default=CavItem(
                        er=val["er"], sigma=val["sigma"], freq=freq * 10 ** 6
                    )
                ),
            )
            foods_base.append(food_tuple)
        name = f"f{freq}"
        dtcls = make_dataclass(
            name,
            foods_base,
        )
        setattr(cfg, name, dtcls())
    return cfg


cfg = make_cfg()
