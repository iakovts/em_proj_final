import numpy as np

from collections import defaultdict

from micwave.util.config import cfg

mur = 1.0  # Relative Permeability
sim = 0.0  # Equivalent magnetic loss


def gpt(var):
    """Translates length from meters to grid points."""
    return int(var / cfg.grid.spacing)


def get_coefficients(freq):
    """Returns the ca, cb, da, db coefficients for each object"""
    if freq == 915:
        coef = cfg.f915
    else:
        coef = cfg.f2450

    objs = ["potato1", "potato2", "burger", "plate", "air"]
    coeffs = defaultdict(dict)

    for obj in objs:
        coeffs["ca"][obj], coeffs["cb"][obj] = cacb(obj, coef)
        coeffs["da"][obj], coeffs["db"][obj] = dadb(obj)
    return coeffs


def cacb(obj, freq):
    obj_c = getattr(freq, obj)  # Object's frequency dependent coeffs
    eaf = cfg.grid.dt * obj_c.sigma / (2 * cfg.const.epsz * obj_c.er)
    ca = (1 - eaf) / (1 + eaf)
    cb = cfg.grid.dt / cfg.const.epsz / obj_c.er / cfg.grid.spacing / (1 + eaf)
    return (ca, cb)


def dadb(obj):
    haf = cfg.grid.dt * sim / (2 * cfg.const.muz * mur)
    da = (1 - haf) / (1 + haf)
    db = cfg.grid.dt / cfg.const.muz / mur / cfg.grid.spacing / (1 + haf)
    return (da, db)


class CustomDefDict(dict):
    """A custom dictionary, similar to `defaultdict` but has access to `key"""

    def __init__(self, factory):
        self.factory = factory

    def __missing__(self, key):
        self[key] = self.factory(key)
        return self[key]


def gaussian_source(size_x, size_y, sigma_x, sigma_y):
    ### NOTE: Not used
    """Creates x-y excitation with gaussian profile on both dimensions"""
    x0 = size_x // 2
    y0 = size_y // 2

    x = np.arange(0, size_x, dtype=float)
    y = np.arange(0, size_y, dtype=float)[:, np.newaxis]

    x -= x0
    y -= y0

    exp_part = x ** 2 / (2 * sigma_x ** 2) + y ** 2 / (2 * sigma_y ** 2)
    return 1 / (2 * np.pi * sigma_x * sigma_y) * np.exp(-exp_part)


def vol(obj):
    """Returns the volume of an object is SI units"""
    if obj.z is not None:
        # Cylindrical
        vol = np.pi * (obj.r ** 2) * obj.z
    else:
        # Spherical
        vol = (4 / 3) * np.pi * (obj.r ** 3)
    return vol


def rotate_plate_clockwise(obj_center, origin, radians):
    """Rotates a set of (x, y) coordinates around a given origin"""
    x, y = obj_center
    offset_x, offset_y = origin
    adjusted_x = x - offset_x
    adjusted_y = y - offset_y
    cos_rad = np.cos(radians)
    sin_rad = np.sin(radians)
    qx = offset_x + cos_rad * adjusted_x + sin_rad * adjusted_y
    qy = offset_y + -sin_rad * adjusted_x + cos_rad * adjusted_y
    return (round(qx, 5), round(qy, 5))


def nsetattr(base, path, value):
    """Accept a dotted path to a nested attribute to set."""
    path, _, target = path.rpartition(".")
    for attrname in path.split("."):
        base = getattr(base, attrname)
    setattr(base, target, value)


def print_tabular(x_headers, y_headers, text):
    print("Printing Results...\n\n")
    row_format = "{:>13.7}" * (len(y_headers) + 1)
    print(row_format.format("AVG SAR", *y_headers))
    for obj, row in zip(x_headers, text):
        print(row_format.format(obj, *row))


def formatted_output(sar):
    x_headers = list(sar[0.0].keys())
    y_headers = list(sar.keys())
    y_headers.extend(["μ", "σ", "σ/μ %"])
    vals = [[d for d in sar[angl].values()] for angl in list(sar.keys())]
    nvals = np.asarray(vals).T
    mean_sar_obj = np.mean(nvals, axis=1)
    std_obj = np.std(nvals, axis=1)
    sigma_mi = 100 * std_obj / mean_sar_obj
    total_vals = np.c_[nvals, mean_sar_obj, std_obj, sigma_mi]
    print_tabular(x_headers, y_headers, total_vals)
