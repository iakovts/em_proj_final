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
