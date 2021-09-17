import fdtd
import numpy as np

from functools import wraps

from micwave.util.config import cfg
from micwave.util.helpers import transform_object


class MicrowaveOven:
    def __init__(self):
        self.foodstuff = ["burger", "potato1", "potato2", "plate"]
        self.grid = fdtd.Grid(
            (cfg.dims.oven.x, cfg.dims.oven.y, cfg.dims.oven.z),
            grid_spacing=cfg.grid.spacing,
        )
        self.min_height = 0  # Counter for z-axis current occupied height.
        self.b_thickness = 5  # Boundary thickness

    def add_boundaries(self):
        self.grid[0:self.b_thickness, :, :] = fdtd.PML(name="pml_xlow")
        self.grid[-self.b_thickness:, :, :] = fdtd.PML(name="pml_xhigh")
        self.grid[:, 0:self.b_thickness, :] = fdtd.PML(name="pml_ylow")
        self.grid[:, -self.b_thickness:, :] = fdtd.PML(name="pml_yhigh")
        self.grid[:, :, 0:self.b_thickness] = fdtd.PML(name="pml_zlow")
        self.grid[:, :, -self.b_thickness:] = fdtd.PML(name="pml_zhigh")
        self.min_height += self.b_thickness

    def add_objects(self):
        for obj in self.foodstuff:
            dims = getattr(cfg.dims, obj)


# def min_h(func):
#     @wraps(func)
#     def add_to_min_height(self, height, *args, **kwargs):
#         self.min_height += height

#     return add_to_min_height


if __name__ == "__main__":
    oven = MicrowaveOven()
    oven.add_boundaries()
    # oven.grid.visualize(z=0)
    # oven.grid[1:100, 2:30, 4:10] = fdtd.AbsorbingObject()
