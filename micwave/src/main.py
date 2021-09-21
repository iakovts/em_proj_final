import fdtd
import numpy as np

from functools import wraps

from micwave.util.config import cfg
from micwave.util.helpers import gpt
from micwave.util.masks import mask_item, obj_on_grid


class MicrowaveOven:
    def __init__(self, freq):
        self.foodstuff = ["plate", "burger", "potato1", "potato2"]
        perm = cond = np.ones(
            (gpt(cfg.dims.oven.x), gpt(cfg.dims.oven.y), gpt(cfg.dims.oven.z))
        )
        print(perm.shape)
        self.grid = fdtd.Grid(
            (cfg.dims.oven.x, cfg.dims.oven.y, cfg.dims.oven.z),
            grid_spacing=cfg.grid.spacing,
            # permittivity=perm,
            # permeability=cond,
        )
        self.min_height = 0  # Counter for z-axis current occupied height.
        self.b_thickness = 5  # Boundary thickness
        self.freq = freq
        self.f_var = None  # Frequency dependent variables of objs
        self.obj_pos = {}  # Contains the grid points of objects
        self.obj_indices = {}  # Object indices, used for post-processing
        if self.freq == 915:
            self.f_var = cfg.f915
        else:
            self.f_var = cfg.f2450

    def add_boundaries(self):
        # fmt: off
        self.grid[0: self.b_thickness, :, :] = fdtd.PML(name="pml_xlow")
        self.grid[-self.b_thickness:, :, :] = fdtd.PML(name="pml_xhigh")
        self.grid[:, 0: self.b_thickness, :] = fdtd.PML(name="pml_ylow")
        self.grid[:, -self.b_thickness:, :] = fdtd.PML(name="pml_yhigh")
        self.grid[:, :, 0: self.b_thickness] = fdtd.PML(name="pml_zlow")
        self.grid[:, :, -self.b_thickness:] = fdtd.PML(name="pml_zhigh")
        self.min_height += self.b_thickness
        # fmt: on

    def obj_slices(self, dims):
        """Returns a tuple of slices, used for a creating a rectangle around an
        object to be placed in the oven"""
        obj_x = slice(
            gpt(dims.center[0]) - gpt(dims.r), gpt(dims.center[0]) + gpt(dims.r)
        )
        obj_y = slice(
            gpt(dims.center[1]) - gpt(dims.r), gpt(dims.center[1]) + gpt(dims.r)
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

    def add_objects(self):
        for obj in self.foodstuff:
            dims = getattr(cfg.dims, obj)
            obj_rect = self.obj_slices(dims)
            obj_mask = mask_item(dims)
            self.obj_pos[obj] = obj_on_grid(
                tuple(rect.start for rect in obj_rect),
                obj_mask[:, :, :, 0],
            )
            obj_perm = obj_cond = np.ones(
                (
                    self.slc_len(obj_rect[0]),
                    self.slc_len(obj_rect[1]),
                    self.slc_len(obj_rect[2]),
                    1,
                )
            )
            obj_perm += obj_mask * (
                getattr(self.f_var, obj).er
            )  # Remove background permittivity
            ### XXX Change this?? XXX
            obj_cond = obj_mask * (getattr(self.f_var, obj).sigma)
            # Add object to grid
            self.grid[obj_rect[0], obj_rect[1], obj_rect[2]] = fdtd.AbsorbingObject(
                permittivity=obj_perm, conductivity=obj_cond, name=obj
            )
            if obj == "plate":
                self.min_height += gpt(dims.z)


if __name__ == "__main__":
    oven = MicrowaveOven(915)
    oven.add_boundaries()
    oven.add_objects()
   # oven.grid.visualize(
   #     z=10, save=True, folder=""
   # )
   # # oven.grid.visualize(z=0)
    # oven.grid[1:100, 2:30, 4:10] = fdtd.AbsorbingObject()
