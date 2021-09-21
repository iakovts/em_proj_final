import numpy as np

from micwave.util.config import cfg

from micwave.util.helpers import gpt


def mask_item(obj):
    if obj.z is not None:
        # Cylindrical object
        return cyl_mask(obj)[:, :, :, None]
        # return cyl_mask(obj)
    else:
        # Spherical object
        return sphere_mask(obj)[:, :, :, None]
        # return sphere_mask(obj)


def sphere_mask(obj):
    """Returns the mask for a spherical object. Assumes a
    dataclass `DimenionsSpher` object as input"""
    r = gpt(obj.r)
    x = y = z = np.arange(-r, r)
    X, Y, Z = np.meshgrid(x, y, z)
    sphere_mask = np.sqrt(X ** 2 + Y ** 2 + Z ** 2) <= r
    return sphere_mask


def cyl_mask(obj):
    """Returns the mask for a cylindrical object. Assumes a
    dataclass `DimenionsSpher` object as input"""
    r, z = map(gpt, [obj.r, obj.z])  # Transform to grid spacing
    x = y = np.arange(-r, r)
    z = np.arange(z)
    X, Y, Z = np.meshgrid(x, y, z)
    cyl_mask = np.sqrt(X ** 2 + Y ** 2) <= r
    return cyl_mask


def obj_on_grid(rect, mask):
    """Returns the grid points of an object on the grid,
    based on its mask.
    args:
      - rect -> tuple: dimensions of rectangle on grid where the
    object is, in the form (X, Y, Z).
      - mask -> np.array: Mask of the object"""
    obj = np.where(mask > 0)
    obj_grid_pts = np.c_[obj]  # Fast equivalent of `np.asarray(list(zip(*obj)))`
    for i in range(3):
        obj_grid_pts[:, i] += rect[i]
    return obj_grid_pts


def obj_indices(grid_pts):
    """Takes a list of grid points as input and returns a tuple of
    arrays that contain the (row, col, aisles), used for indexing"""
    return tuple(grid_pts[:, i] for i in range(3))
