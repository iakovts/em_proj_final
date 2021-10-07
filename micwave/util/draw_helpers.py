import numpy as np
import plotly.graph_objects as go

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
            name="yolo",
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
    x = 169 * np.ones(y.shape)
    fig.add_trace(go.Surface(x=x, y=y, z=z, showscale=False, colorscale=bright_blue))


def update_layout_grid(fig):
    fig.update_layout(
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
