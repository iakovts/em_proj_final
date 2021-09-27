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
        # self.source_power = 0.5  # Source power in (V/m)
        if self.freq == 915:
            self.f_var = cfg.f915
        else:
            self.f_var = cfg.f2450
        self.coef = get_coefficients(self.freq)
        self.freq *= 10 ** 6
        self.wavelength = cfg.const.c / self.freq
        self.period = 1 / self.freq
        self.sar = {}
        self.heatmaps = []

        # Set dx to according to minimum wavelength
        # cfg.grid.spacing = round ((self.wavelength / np.sqrt(self.f_var.potato1.er)) / 10, 3)

    def init_grid(self):
        self.grid_dims = {k: gpt(v) for k, v in asdict(cfg.dims.oven).items()}
        self.Nx, self.Ny, self.Nz = (
            self.grid_dims["x"],
            self.grid_dims["y"],
            self.grid_dims["z"],
        )

    def init_fields(self):
        self.E = OrderedDict()
        self.E["x"] = np.zeros((self.Nx, self.Ny + 1, self.Nz + 1))
        self.E["y"] = np.zeros((self.Nx + 1, self.Ny, self.Nz + 1))
        self.E["z"] = np.zeros((self.Nx + 1, self.Ny + 1, self.Nz))

        self.H = OrderedDict()
        self.H["x"] = np.zeros((self.Nx + 1, self.Ny, self.Nz))
        self.H["y"] = np.zeros((self.Nx, self.Ny + 1, self.Nz))
        self.H["z"] = np.zeros((self.Nx, self.Ny, self.Nz + 1))

    # def init_coeffs_fields(self):

    def init_space(self):
        """Initializes the space of the simulation taking into account the
        coefficients in its grid, with objects included"""
        # self.coef_fields = defaultdict(dict)
        # self.coef_fields = CustomDefDict
        self.coef_fields = OrderedDict()
        for c in ["caE", "cbE", "daH", "dbH"]:
            self.coef_fields[c] = self.coef[c[:-1]]["air"] * np.ones(
                (self.Nx, self.Ny, self.Nz)
            )
            # Initialize everything with default (air) values.
            # self.coef_fields[c] = CustomDefDict(
            #     lambda x: self.coef[c[:-1]]["air"] * np.ones(getattr(self, f"N{idx}"))
            # )
            # for idx in ["x", "y", "z"]:
            #     self.coef_fields[c][idx]

    def add_objects_in_field(self):
        """Adds the coefficients of the objects to the fields."""
        self.add_objects()
        for obj in self.foodstuff:
            for c in ["caE", "cbE", "daH", "dbH"]:
                self.coef_fields[c][self.obj_indices[obj]] = self.coef[c[:-1]][obj]

    def update_E(self):
        ie, je, ke, = (
            self.Nx,
            self.Ny,
            self.Nz,
        )
        ib, jb, kb = (ie + 1, je + 1, ke + 1)
        self.E["x"][:ie, 1:je, 1:ke] = (
            self.coef_fields["caE"][:ie, 1:je, 1:ke] * self.E["x"][:ie, 1:je, 1:ke]
        ) + self.coef_fields["cbE"][:ie, 1:je, 1:ke] * (
            self.H["z"][:ie, 1:je, 1:ke]
            - self.H["z"][:ie, : je - 1, 1:ke]
            + self.H["y"][:ie, 1:je, : ke - 1]
            - self.H["y"][:ie, 1:je, 1:ke]
        )

        self.E["y"][1:ie, :je, 1:ke] = (
            self.coef_fields["caE"][1:ie, :je, 1:ke] * self.E["y"][1:ie, :je, 1:ke]
        ) + self.coef_fields["cbE"][1:ie, :je, 1:ke] * (
            self.H["x"][1:ie, :je, 1:ke]
            - self.H["x"][1:ie, :je, : ke - 1]
            + self.H["z"][: ie - 1, :je, 1:ke]
            - self.H["z"][1:ie, :je, 1:ke]
        )

        self.E["z"][1:ie, 1:je, :ke] = (
            self.coef_fields["caE"][1:ie, 1:je, :ke] * self.E["z"][1:ie, 1:je, :ke]
        ) + self.coef_fields["cbE"][1:ie, 1:je, :ke] * (
            self.H["x"][1:ie, : je - 1, :ke]
            - self.H["x"][1:ie, 1:je, :ke]
            + self.H["y"][1:ie, 1:je, :ke]
            - self.H["y"][: ie - 1, 1:je, :ke]
        )

    def update_H(self):
        ie, je, ke, = (
            self.Nx,
            self.Ny,
            self.Nz,
        )
        ib, jb, kb = (ie + 1, je + 1, ke + 1)
        self.H["x"][1:ie, :je, :ke] = (
            self.coef_fields["daH"][1:ie, :je, :ke] * self.H["x"][1:ie, :je, :ke]
        ) + self.coef_fields["dbH"][1:ie, :je, :ke] * (
            self.E["y"][1:ie, :je, 1:kb]
            - self.E["y"][1:ie, :je, :ke]
            + self.E["z"][1:ie, :je, :ke]
            - self.E["z"][1:ie, 1:jb, :ke]
        )

        self.H["y"][:ie, 1:je, :ke] = (
            self.coef_fields["daH"][:ie, 1:je, :ke] * self.H["y"][:ie, 1:je, :ke]
        ) + self.coef_fields["dbH"][:ie, 1:je, :ke] * (
            self.E["x"][:ie, 1:je, :ke]
            - self.E["x"][:ie, 1:je, 1:kb]
            + self.E["z"][1:ib, 1:je, :ke]
            - self.E["z"][:ie, 1:je, :ke]
        )

        self.H["z"][:ie, :je, 1:ke] = (
            self.coef_fields["daH"][:ie, :je, 1:ke] * self.H["z"][:ie, :je, 1:ke]
        ) + self.coef_fields["dbH"][:ie, :je, 1:ke] * (
            self.E["x"][:ie, 1:jb, 1:ke]
            - self.E["x"][:ie, :je, 1:ke]
            + self.E["y"][:ie, :je, 1:ke]
            - self.E["y"][1:ib, :je, 1:ke]
        )

    def update_source(self, N):
        """Updates the source on the grid. `N` is the timestep"""
        rtau = 50.0e-12
        tau = rtau / cfg.grid.dt
        ndelay = 3 * tau
        src_const = cfg.grid.dt * 3.0e11

        src_pos_x = slice(
            gpt(cfg.grid.src_corn.x), gpt(cfg.grid.src_corn.x) + gpt(cfg.dims.source.x)
        )
        src_pos_y = slice(
            gpt(cfg.grid.src_corn.y), gpt(cfg.grid.src_corn.y) + gpt(cfg.dims.source.y)
        )
        src_pos_z = gpt(cfg.grid.src_corn.z) - 1
        # return (src_pos_x, src_pos_y, src_pos_z)
        self.E["y"][
            src_pos_x, src_pos_y, src_pos_z
        ] = self.source_power * gaussian_source(
            self.slc_len(src_pos_x),
            self.slc_len(src_pos_y),
            10,
            self.slc_len(src_pos_y),
        )

    def update_source_2(self, N):
        src_c = cfg.grid.src_corn  # Coordinates of source "lower-left" corner
        src_d = cfg.dims.source  # Dimensions of source
        src_slc_x = slice(gpt(src_c.x), gpt(src_c.x) + gpt(src_d.x))
        src_slc_y = slice(gpt(src_c.y), gpt(src_c.y) + gpt(src_d.y))
        src_slc_z = gpt(src_c.z)
        # print(src_slc_x, src_slc_y, src_slc_z)

        # source_area = src_d.x * src_d.y
        x_pts = np.arange(src_c.x, src_c.x + src_d.x, cfg.grid.spacing)
        y_pts = np.arange(src_c.y, src_c.y + src_d.y, cfg.grid.spacing)
        omega = 2 * np.pi * self.freq
        # beta = (2 * np.pi) / self.wavelength * 0
        beta = 0

        sin_part = np.zeros((gpt(src_d.x), gpt(src_d.y)))
        # cos_part = np.zeros((gpt(src_d.y), gpt(src_d.y)))

        # sin_part[:, :] = np.sin(np.pi * (x_pts - src_c.x) / source_area)
        sin_part[:, :] = np.sin(np.pi * (y_pts - src_c.y) / src_d.y)
        cos_part = np.cos(omega * (N + 1) * cfg.grid.dt - beta * src_c.z)
        total = self.source_power * sin_part * cos_part
        # print(total)
        self.heatmaps.append(total)
        self.E["y"][src_slc_x, src_slc_y, src_slc_z] = total

    def calc_sar(self):
        for obj in self.foodstuff:
            total_E = 0
            for energy in self.E.values():
                obj_E = np.abs(energy[self.obj_indices[obj]]) ** 2
                total_E += np.sum(obj_E)
            obj_vol = vol(getattr(cfg.dims, obj))
            self.sar[obj] = (
                (1 / obj_vol)
                * getattr(self.f_var, obj).sigma
                * total_E
                * cfg.grid.spacing ** 3
            ) / (getattr(self.f_var, obj).dens)
            # self.sar[obj] = (
            #     (getattr(self.f_var, obj).sigma * total_E)
            #     / (getattr(self.f_var, obj).dens * len(self.obj_pos[obj]))
            # )

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

    def _init(self):
        self.init_grid()
        self.init_fields()
        self.init_space()
        self.add_objects_in_field()
        timesteps = int(
            2 * (cfg.dims.oven.x / self.wavelength) * self.period / cfg.grid.dt
        )
        print(cfg.grid.dt, cfg.grid.spacing, timesteps, self.wavelength)
        for N in range(timesteps):
            # for N in range(400):
            print(N)
            self.update_E()
            self.update_source_2(N)
            self.update_H()
        self.calc_sar()


if __name__ == "__main__":
    oven = MicrowaveOven(2450)
    oven._init()
