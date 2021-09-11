from dataclasses import dataclass, field, make_dataclass

from typing import List, Any

FOODSTUFF_CFG = {
    915: {
        "potato": {
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
        "potato": {
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


@dataclass(eq=False)
class DimBase:
    # All dimensions in cm
    oven: DimensionsRect = field(default=DimensionsRect(x=17.2, y=17.2, z=14.9))
    wg: DimensionsRect = field(default=DimensionsRect(x=4.6, y=9.2, z=4.9))
    burger: DimensionsSpher = field(default=DimensionsSpher(r=4, z=2))
    potato: DimensionsSpher = field(default=DimensionsSpher(r=2))
    plate: DimensionsSpher = field(default=DimensionsSpher(r=14, z=1))


@dataclass
class CfgBase:
    f915: Any = field(init=False)
    f2450: Any = field(init=False)
    dims: DimBase = field(default=DimBase())


def make_cfg(freq):
    cfg = CfgBase()
    for freq, food in FOODSTUFF_CFG.items():
        foods_base = []
        for obj, val in food.items():
            food_tuple = (
                obj,
                CavItem,
                field(default=CavItem(er=val["er"], sigma=val["sigma"], freq=freq)),
            )
            foods_base.append(food_tuple)
        name = f"f{freq}"
        dtcls = make_dataclass(
            name,
            foods_base,
        )
        setattr(cfg, name, dtcls())
    return cfg
