import copy
import numpy as np

from collections import OrderedDict
from dataclasses import asdict

from micwave.util.config import cfg
from micwave.util.helpers import (
    CustomDefDict,
    gaussian_source,
    get_coefficients,
    gpt,
    vol,
)
from micwave.util.masks import mask_item, obj_on_grid, obj_indices


class MicrowaveOven:
    def __init__(self, freq):
        # cfg = cfg
        self.foodstuff = ["plate", "burger", "potato1", "potato2"]
        self.min_height = 1  # Counter for z-axis current occupied height.
        self.b_thickness = 5  # Boundary thickness
        self.freq = freq
        self.f_var = None  # Frequency dependent variables of objs
        self.obj_pos = {}  # Contains the grid points of objects
        self.obj_indices = {}  # Object indices, used for post-processing
        self.obj_max_E = {}  # Holds arrays with the max values of E for objs
        self.source_power = 117.0  # Source power in (V/m)
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

    def init_grid(self):
        """Transform simulation space dimensions to grid points based on
        grid spacing."""
        self.grid_dims = {k: gpt(v) for k, v in asdict(cfg.dims.oven).items()}
        self.Nx, self.Ny, self.Nz = (
            self.grid_dims["x"],
            self.grid_dims["y"],
            self.grid_dims["z"],
        )

    def init_fields(self):
        """Initialize E and H fields to 0."""
        self.E = OrderedDict()
        self.E["x"] = np.zeros((self.Nx, self.Ny + 1, self.Nz + 1))
        self.E["y"] = np.zeros((self.Nx + 1, self.Ny, self.Nz + 1))
        self.E["z"] = np.zeros((self.Nx + 1, self.Ny + 1, self.Nz))

        self.H = OrderedDict()
        self.H["x"] = np.zeros((self.Nx + 1, self.Ny, self.Nz))
        self.H["y"] = np.zeros((self.Nx, self.Ny + 1, self.Nz))
        self.H["z"] = np.zeros((self.Nx, self.Ny, self.Nz + 1))

    def init_space(self):
        """Initialize coefficient fields."""
        self.coef_fields = OrderedDict()
        for c in ["caE", "cbE", "daH", "dbH"]:
            self.coef_fields[c] = self.coef[c[:-1]]["air"] * np.ones(
                (self.Nx, self.Ny, self.Nz)
            )

    def add_objects_in_field(self):
        """Adds the coefficients of the objects to the fields."""
        self.add_objects()
        for obj in self.foodstuff:
            for c in ["caE", "cbE", "daH", "dbH"]:
                self.coef_fields[c][self.obj_indices[obj]] = self.coef[c[:-1]][obj]

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
        object to be placed in the oven. Used for masking."""
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

    def update_E(self):
        """Update E fields using FDTD equations"""
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
        """Update H fields using FDTD equations"""
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
        src_c = cfg.grid.src_corn  # Coordinates of source "lower-left" corner
        src_d = cfg.dims.source  # Dimensions of source

        src_slc_x = gpt(src_c.x)
        src_slc_y = slice(gpt(src_c.y), gpt(src_c.y) + gpt(src_d.y))
        src_slc_z = slice(gpt(src_c.z), gpt(src_c.z) + gpt(src_d.z))

        y_pts = np.arange(src_c.y, src_c.y + src_d.y, cfg.grid.spacing)
        omega = 2 * np.pi * self.freq

        src_y = np.sin(np.pi * (y_pts - src_c.y) / src_d.y)
        sin_part = np.transpose([src_y] * gpt(src_d.z))
        cos_part = np.cos(omega * (N + 1) * cfg.grid.dt)
        total = self.source_power * sin_part * cos_part
        self.heatmaps.append(total)
        self.E["y"][src_slc_x, src_slc_y, src_slc_z] = total

    def calc_sar(self):
        """Calculates the SAR value for each object, based on the maximum
        value of the fields in their respective voxels."""
        for obj in self.foodstuff:
            total_E = 0
            for energy in self.max_E.values():
                obj_E = energy[self.obj_indices[obj]] ** 2
                total_E += np.sum(obj_E)
            obj_vol = vol(getattr(cfg.dims, obj))
            self.sar[obj] = (
                (1 / obj_vol)
                * getattr(self.f_var, obj).sigma
                * total_E
                * cfg.grid.spacing ** 3
            ) / (getattr(self.f_var, obj).dens)

    def slc_len(self, slc):
        """Returns the length of a slice object"""
        return int(slc.stop - slc.start)

    def calc_tot_E(self, obj):
        """Calculates the total electric field E_0^2 for a given object"""
        tot = 0
        for val in list(self.E.values()):
            tot += val[self.obj_indices[obj]] ** 2
        return tot

    def calc_tot_E_pt(self, pt):
        """Calculates the RSS total electric field for a given voxel"""
        tot = 0
        for val in list(self.E.values()):
            tot += val[(*pt,)] ** 2
        return np.sqrt(tot)

    def compare_E(self):
        """Updates the maximum absolute value for each E field"""
        for k, v in self.max_E.items():
            self.max_E[k] = np.maximum(self.max_E[k], np.absolute(self.E[k]))

    def _init(self):
        self.init_grid()
        self.init_fields()
        self.init_space()
        self.add_objects_in_field()
        self.max_E = copy.deepcopy(self.E)

    def run(self):
        """Actually run the simulation"""
        self._init()
        timesteps = 2 * int(
            2
            * (cfg.dims.oven.x / self.wavelength)
            * self.period
            / cfg.grid.dt
        )
        print("Total Timesteps: ", timesteps)
        self.track_steady = np.zeros(timesteps)
        for N in range(timesteps):
            self.update_E()
            self.update_source(N)
            self.update_H()
            self.track_steady[N] = self.calc_tot_E_pt([50, 50, 50])
            if N >= 800:
                # Assume a steady state after 800 timesteps and
                # start calculating maximums for E fields now.
                self.compare_E()
        self.calc_sar()
