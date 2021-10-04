import numpy as np
import argparse

from micwave.src.microwave_oven import MicrowaveOven

# from micwave.util.config import make_cfg
import micwave.util.config as config
from micwave.util.helpers import rotate_plate_clockwise, nsetattr, print_tabular


def run(freq=None):
    cfg = config.cfg

    if freq is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--frequency", type=int, default=915, choices=[915, 2450])
        args = parser.parse_args()
        freq = args.frequency

    oven = MicrowaveOven(freq, cfg)
    angles = [i * (np.pi / 2) for i in range(4)]
    objects = oven.foodstuff[:]
    objects.remove("plate")
    total_sar = {}
    coef_snapshots = []
    E_snapshots = []
    for angle in angles:
        for obj in objects:
            # Rotate all object taking as origin the center of the plate
            obj_cntr = rotate_plate_clockwise(
                getattr(cfg.dims, obj).center, cfg.dims.plate.center, angle
            )
            nsetattr(cfg.dims, obj + ".center", obj_cntr)
        oven = MicrowaveOven(args.frequency, cfg)
        print(
            f"Oven configuration: \nFrequency {oven.freq} Hz |"
            f" Source Power: {oven.source_power} V/m | dx = {cfg.grid.spacing} m | "
            f" dt = {cfg.grid.dt} s |"
            f" Oven dimensions (x, y, z) = {cfg.dims.oven.x, cfg.dims.oven.y, cfg.dims.oven.z}m | "
            f"Current rotation angle: {np.degrees(angle)}.\n"
            "Starting Simulation..."
        )
        oven.run()
        total_sar[np.degrees(angle)] = oven.sar
        coef_snapshots.append(oven.coef_fields)
        E_snapshots.append(oven.E)
    return total_sar, coef_snapshots, E_snapshots, oven


if __name__ == "__main__":
    sar, snap, E_snap, oven = run()
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
