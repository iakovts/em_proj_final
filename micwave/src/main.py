import argparse
import numpy as np

from micwave.src.microwave_oven import MicrowaveOven

import micwave.util.config as config
from micwave.util.helpers import rotate_plate_clockwise, nsetattr, formatted_output


def run(freq=None):
    """Entrypoing for the simulation. Returns some useful data for visualization"""
    cfg = config.cfg

    if freq is None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-f", "--frequency", type=int, default=915, choices=[915, 2450], required=False,
        )
        args = parser.parse_args()
        freq = args.frequency

    oven = MicrowaveOven(freq)  # Used only to get `foodstuff` var here.
    angle = np.pi / 2  # Since the center positions are saved, always rotate by 90
    objects = oven.foodstuff[:]
    objects.remove("plate")

    # Variables used for visualization later.
    total_sar = {}
    ovens = []
    rot_count = 0

    # Rotate 3 times
    for _ in range(4):
        for obj in objects:

            # Rotate all objects taking as origin the center of the plate
            if rot_count != 0:
                obj_cntr = rotate_plate_clockwise(
                    getattr(cfg.dims, obj).center, cfg.dims.plate.center, angle
                )
                nsetattr(cfg.dims, obj + ".center", obj_cntr)
        oven = MicrowaveOven(freq)
        print(
            f"Oven configuration: \nFrequency {oven.freq} Hz |"
            f" Source Power: {oven.source_power} V/m | dx = {cfg.grid.spacing} m | "
            f" dt = {cfg.grid.dt} s |"
            f" Oven dimensions (x, y, z) = {cfg.dims.oven.x, cfg.dims.oven.y, cfg.dims.oven.z}m | "
            f"Current rotation angle: {np.degrees(angle) * rot_count}.\n"
            "Starting Simulation..."
        )
        oven.run()
        total_sar[np.degrees(angle) * rot_count] = oven.sar
        ovens.append(oven)
        rot_count += 1

    return total_sar, ovens


if __name__ == "__main__":
    sar, snap, E_snap, oven = run()
    formatted_output(sar)
