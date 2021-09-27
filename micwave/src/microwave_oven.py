import numpy as np
import os

from collections import OrderedDict, defaultdict
from dataclasses import asdict

from matplotlib import pyplot as plt


from micwave.util.config import cfg
from micwave.util.helpers import (
    gpt,
    get_coefficients,
    gaussian_source,
    CustomDefDict,
    vol,
)
from micwave.util.masks import mask_item, obj_on_grid, obj_indices


class MicrowaveOven:
    def __init__(self, freq):
        self.foodstuff = ["plate", "burger", "potato1", "potato2"]
        self.min_height = 0  # Counter for z-axis current occupied height.
        self.b_thickness = 5  # Boundary thickness
        self.freq = freq
        self.f_var = None  # Frequency dependent variables of objs
        self.obj_pos = {}  # Contains the grid points of objects
        self.obj_indices = {}  # Object indices, used for post-processing
        self.source_power = 117.0  # Source power in (V/m)
        if self.freq == 915:
            self.f_var = cfg.f915
        else:
            self.f_var = cfg.f2450
        self.freq *= 10 ** 6

    def add_boundaries(self):
        # fmt: off
        # self.grid[0: self.b_thickness, :, :] = fdtd.PeriodicBoundary(name="pml_xlow")
        # self.grid[-self.b_thickness:, :, :] = fdtd.PeriodicBoundary(name="pml_xhigh")
        # self.grid[:, 0: self.b_thickness, :] = fdtd.PeriodicBoundary(name="pml_ylow")
        # self.grid[:, -self.b_thickness:, :] = fdtd.PeriodicBoundary(name="pml_yhigh")
        # self.grid[:, :, 0: self.b_thickness] = fdtd.PeriodicBoundary(name="pml_zlow")
        # self.grid[:, :, -self.b_thickness:] = fdtd.PeriodicBoundary(name="pml_zhigh")
        self.grid[0, :, :] = fdtd.PeriodicBoundary(name="pml_xlow")
        # self.grid[-1, :, :] = fdtd.PeriodicBoundary(name="pml_xhigh")
        self.grid[:, 0, :] = fdtd.PeriodicBoundary(name="pml_ylow")
        # self.grid[:, -1, :] = fdtd.PeriodicBoundary(name="pml_yhigh")
        self.grid[:, :, 0] = fdtd.PeriodicBoundary(name="pml_zlow")
        # self.grid[:, :, -1] = fdtd.PeriodicBoundary(name="pml_zhigh")
        self.min_height += self.b_thickness
        # fmt: on

    def add_source(self):
        # lower left corner of source on y-z plane
        source_corner = (gpt(0.01), gpt(0.01))
        # source_x = slice(self.b_thickness, gpt(cfg.dims.source.x))
        source_y = slice(source_corner[0], source_corner[0] + gpt(cfg.dims.source.y))
        source_z = slice(source_corner[1], source_corner[1] + gpt(cfg.dims.source.z))
        self.grid[self.b_thickness: self.b_thickness+1, source_y, source_z] = fdtd.PlaneSource(
            period=(1 / self.freq), power=self.source_power, name="Source"
        )

    def add_objects(self):
        for obj in self.foodstuff:
            dims = getattr(cfg.dims, obj)
            obj_rect = self.obj_slices(dims)
            obj_mask = mask_item(dims)

            # Get the grid points of the objects and their indices
            self.obj_pos[obj] = obj_on_grid(
                tuple(rect.start for rect in obj_rect),
                obj_mask[:, :, :, 0],
            )
            self.obj_indices[obj] = obj_indices(self.obj_pos[obj])

            if obj == "plate":
                self.min_height += gpt(dims.z)

    def obj_slices(self, dims):
        """Returns a tuple of slices, used for a creating a rectangle around an
        object to be placed in the oven"""
        obj_x, obj_y = (
            slice(gpt(dims.center[i]) - gpt(dims.r), gpt(dims.center[i]) + gpt(dims.r))
            for i in range(2)
        )
        if dims.z is not None:
            # Cylindrical
            obj_z = slice(self.min_height, self.min_height + gpt(dims.z))
        else:
            # Spherical
            obj_z = slice(self.min_height, self.min_height + 2 * gpt(dims.r))
        return (obj_x, obj_y, obj_z)

    def slc_len(self, slc):
        return int(slc.stop - slc.start)

    def initialize(self):
        self.add_boundaries()
        self.add_source()
        self.add_objects()

    def run(self):
        self.initialize()
        self.grid.run(total_time=200)


if __name__ == "__main__":
    oven = MicrowaveOven(915)
    oven.add_boundaries()
    oven.add_source()
    oven.add_objects()
    oven.grid.visualize(z=10, save=True, folder=os.getcwd())
    oven.grid.run(total_time=200)
# # oven.grid.visualize(z=0)
# oven.grid[1:100, 2:30, 4:10] = fdtd.AbsorbingObject()
