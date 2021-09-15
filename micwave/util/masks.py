import numpy as np

from config import cfg

from matplotlib import pyplot as plt



def sphere_mask(r, pts, grid_slice, perm, cond):
    x = y = z = np.linspace(-r, r, pts)
    X, Y, Z = np.meshgrid(x, y, z)
    sphere_mask = np.sqrt(X**2 + Y**2 + Z**2) <= r
    perm_mat = np.ones((pts, pts, pts))
    perm_mat = sphere_mask * perm
    cond_mat = np.ones((pts, pts, pts))
    cond_mat = sphere_mask * cond
    # return sphere_mask

