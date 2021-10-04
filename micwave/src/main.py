import numpy as np
import argparse

from micwave.src.microwave_oven import MicrowaveOven

# from micwave.util.config import make_cfg
import micwave.util.config as config
from micwave.util.helpers import rotate_plate_clockwise, nsetattr, formatted_output


def run(freq=None):
    """Entrypoing for the simulation. Returns some useful data for visualization"""
    cfg = config.cfg

    if freq is None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-f", "--frequency", type=int, default=915, choices=[915, 2450]
        )
        args = parser.parse_args()
        freq = args.frequency

    oven = MicrowaveOven(freq, cfg)  # Used only to get `foodstuff` var here.
    angles = [i * (np.pi / 2) for i in range(4)]
    objects = oven.foodstuff[:]
    objects.remove("plate")

    # Variables used for visualization later.
    total_sar = {}
    coef_snapshots = []
    E_snapshots = []
    for angle in angles:
        for obj in objects:
            # Rotate all objects taking as origin the center of the plate
            obj_cntr = rotate_plate_clockwise(
                getattr(cfg.dims, obj).center, cfg.dims.plate.center, angle
            )
            nsetattr(cfg.dims, obj + ".center", obj_cntr)
        oven = MicrowaveOven(freq, cfg)
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
    formatted_output(sar)
