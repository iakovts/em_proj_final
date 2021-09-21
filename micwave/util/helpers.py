from micwave.util.config import cfg


def gpt(var):
    """Translates length from meters to grid points."""
    return int(var / cfg.grid.spacing)
