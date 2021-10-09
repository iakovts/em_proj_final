import numpy as np
import plotly.graph_objects as go

from plotly.subplots import make_subplots

from micwave.util.helpers import gpt


def draw_walls(fig):
    # x-wall
    bright_pink = [[0, "#FF007F"], [1, "#FF007F"]]
    y, z = np.meshgrid(np.arange(170), np.arange(150))
    fig.add_trace(
        go.Surface(
            x=[170] * 170,
            y=y,
            z=z,
            showscale=False,
            colorscale=bright_pink,
        )
    )
    # y-wall
    x, z = np.meshgrid(np.arange(170), np.arange(150))
    fig.add_trace(
        go.Surface(x=x, y=[170] * 170, z=z, showscale=False, colorscale=bright_pink)
    )
    # z (floor)
    x, y = np.meshgrid(np.arange(170), np.arange(170))
    z = x * 0
    fig.add_trace(go.Surface(x=x, y=y, z=z, showscale=False, colorscale=bright_pink))


def draw_objects(fig, obj_indices):
    for name, obj_ind in list(obj_indices.items()):
        fig.add_trace(go.Scatter3d(x=obj_ind[0], y=obj_ind[1], z=obj_ind[2], name=name))


def draw_source(fig, cfg):
    # light_yellow = [[0, "#FFDB58"], [1, "#FFDB58"]]
    bright_blue = [[0, "#7DF9FF"], [1, "#7DF9FF"]]
    oven_corner = cfg.grid.src_corn
    oven_dims = cfg.dims.source
    y_pts = np.arange(gpt(oven_corner.y), gpt(oven_corner.y) + gpt(oven_dims.y))
    z_pts = np.arange(gpt(oven_corner.z), gpt(oven_corner.z) + gpt(oven_dims.z))
    y, z = np.meshgrid(y_pts, z_pts)
    x = 169 * np.ones(
        y.shape
    )  # For visibility purposes, the source is a grid point "outside" its pos
    fig.add_trace(go.Surface(x=x, y=y, z=z, showscale=False, colorscale=bright_blue))


def draw_steady(oven_data):
    # fig = go.Figure(go.Scatter(x=np.arange(len(data)), y=data, mode="lines"))
    fig = go.Figure()
    for oven in oven_data:
        fig.add_trace(
            go.Scatter(
                x=np.arange(len(oven.track_steady)),
                y=oven.track_steady,
                mode="lines",
                name=f"f={oven.freq / 10 ** 6:.0f}MHz",
            )
        )
    # Add a line at x=800
    fig.add_trace(go.Scatter(x=[800, 800], y=[0, 20]))
    fig.update_layout(
        title=f"Electric Fields RSS at (50, 50, 50) over all timesteps.",
        yaxis_title="$E_{RSS}$ V/m",
        xaxis_title="timesteps",
    )
    return fig


def draw_source_snap(source_snap):
    snap_N = len(source_snap[0])
    freqs = [915, 2450]
    N = [10, 120, 250]
    subp_titles = []
    for i in N:
        subp_titles.extend([f"f={freq} N={i}" for freq in freqs])
    fig = make_subplots(rows=3, cols=2, subplot_titles=subp_titles, shared_yaxes=True)
    for j in range(3):
        for i in range(2):
            fig.add_trace(
                go.Heatmap(
                    z=source_snap[i][N[j]].T,
                    coloraxis="coloraxis",
                    colorbar={"title": "V/m"},
                ),
                row=j + 1,
                col=i + 1,
            )
    fig.update_layout(
        title="Source Snapshots for different frequencies and timesteps",
        coloraxis={"colorscale": "Inferno"},
    )
    fig.update_xaxes(title_text="y")
    fig.update_yaxes(title_text="z")
    return fig


def draw_E(E, offset, f, Eaxis="y", draw_plane="z", is_max=False):
    """Draws a heatmap of the Electric fields. Can draw all planes and E-axis or E-RSS.
    Args:
    - E -> list: List of dictionaries containing the electric field values.
    - offset -> int : plane 'distance' from 0.
    - f -> str : frequncy, only used for title.
    - Eaxis -> str: 'x', 'y', 'z' or 'rss'. Electric field axis to take into account
    - draw_plane -> str : View plane
    - is_max -> bool : If E_max fields are provided, change title."""
    plane_dict = {"x": 0, "y": 1, "z": 2}
    slc = tuple(
        [offset if idx == plane_dict[draw_plane] else slice(None) for idx in range(3)]
    )
    N = [0, 90, 180, 270]
    subp_titles = [f"f={f}MHz angle={i} z={offset}" for i in N]
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=subp_titles,
        shared_yaxes=True,
    )
    cnt = 0
    E_val = lambda cnt: E[cnt][Eaxis] if Eaxis != "rss" else total_E(E[cnt])
    for j in range(2):
        for i in range(2):
            fig.add_trace(
                go.Heatmap(
                    z=E_val(cnt)[slc].T,
                    coloraxis="coloraxis",
                    colorbar={"title": "V/m"},
                ),
                row=j + 1,
                col=i + 1,
            )
            cnt += 1

    title = f"E_{Eaxis} view for different angles at {draw_plane}={offset} plane"
    if is_max:
        title += " and max E values for field used for calculating SAR"
    fig.update_layout(
        title=f"E_{Eaxis} view for different angles at {draw_plane}={offset} plane",
        coloraxis={"colorscale": "Inferno"},
    )
    return fig


def update_layout_grid(fig):
    fig.update_layout(
        title="Microwave Oven Layout before rotations",
        scene=dict(
            xaxis=dict(
                nticks=20,
                range=[0, 170],
            ),
            yaxis=dict(
                nticks=20,
                range=[0, 170],
            ),
            zaxis=dict(
                nticks=20,
                range=[0, 150],
            ),
        ),
        width=700,
        margin=dict(r=20, l=10, b=10, t=10),
    )


def total_E(E):
    # RSS total electric field
    tot = 0
    for k, val in list(E.items()):
        tot += val[:170, :170, :150] ** 2
    return np.sqrt(tot)
