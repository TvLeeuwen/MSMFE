"""Definitions for data visualization in streamlit"""

# Imports ---------------------------------------------------------------------
import os
import time
import pandas as pd
import pyvista as pv
import streamlit as st
import multiprocessing
import plotly.colors as pc
import plotly.express as px
from stpyvista import stpyvista
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

from pathlib import Path
from src.MSM.sto_generator import read_input
from src.MSM.generate_force_vector_gif import generate_vector_gif


# Defs ------------------------------------------------------------------------
def update_fig_layout(fig):
    fig.update_layout(
        height=1000,
        xaxis_title="Time (s)",
        yaxis_title="Value",
        legend_title="Variables",
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=-0.1,
            xanchor="right",
            x=0.5,
            itemsizing="constant",
            traceorder="grouped",
        ),
    )


def visual_compare_timeseries(sto1, sto2, group_legend):
    df, _ = read_input(sto1)
    df2, _ = read_input(sto2)

    fig = go.Figure()

    color_scale = [hex[1] for hex in pc.get_colorscale("Viridis")]

    for column in df.columns:
        if column != "time":
            legend = column if group_legend else f"Input: {column}"
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color_scale[2]),
                    name=f"Input: {column}",
                    legendgroup=legend,
                    hovertext=f"{column.split('/')[-2]}: {column.split('/')[-1]}",
                )
            )

    for column in df2.columns:
        if column != "time":
            legend = column if group_legend else f"Output: {column}"
            fig.add_trace(
                go.Scatter(
                    x=df2.index,
                    y=df2[column],
                    mode="lines",
                    line=dict(color=color_scale[-3]),
                    name=f"Output: {column}",
                    legendgroup=legend,
                    hovertext=f"{column.split('/')[-2]}: {column.split('/')[-1]}",
                )
            )

    update_fig_layout(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def visual_muscle_data(sto1, group_legend=False):
    df, _ = read_input(sto1)

    # Required for a consistent color index
    columns = set()
    for column in df.columns:
        if column != "time":
            columns.add(column.split("|")[0])
    colors = px.colors.sample_colorscale(
        "viridis", [n / (len(columns) - 1) for n in range(len(columns))]
    )
    color_map = {col: colors[i] for i, col in enumerate(columns)}

    fig = go.Figure()
    for column in df.columns:
        if column != "time":
            state_name = column.split("|")[1] if group_legend else column
            muscle = column.split("|")[0]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color_map[muscle]),
                    name=column,
                    legendgroup=state_name,
                    hovertext=column.split('/')[-1],
                )
            )
    update_fig_layout(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def visual_force_vector_gif(
    mesh_file,
    muscle_force_path,
    force_origins_path,
    force_vectors_path,
    output_path,
):
    st.session_state.gif_path = os.path.join(
        output_path, f"{Path(force_vectors_path).stem}.gif"
    )

    process = multiprocessing.Process(
        target=generate_vector_gif,
        args=(
            mesh_file,
            muscle_force_path,
            force_origins_path,
            force_vectors_path,
            st.session_state.gif_path,
        ),
    )
    process.start()
    with st.spinner("Generating GIF..."):
        while process.is_alive():
            time.sleep(0.1)
    process.join()


def visual_toi_selector(
    df,
    group_legend=False,
):
    columns = set()
    for column in df.columns:
        if column != "time":
            columns.add(column.split("|")[0])
    colors = px.colors.sample_colorscale(
        "viridis", [n / (len(columns) - 1) for n in range(len(columns))]
    )
    st.session_state.color_map = {col: colors[i] for i, col in enumerate(columns)}

    fig = go.Figure()
    fig.add_vline(
        x=st.session_state.toi,
        line_width=3,
        line_dash="dash",
        line_color="white",
    )
    for column in df.columns:
        if column != "time":
            state_name = column.split("|")[1] if group_legend else column
            muscle = column.split("|")[0]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=st.session_state.color_map[muscle]),
                    name=muscle.split("/")[2],
                    legendgroup=state_name,
                )
            )
    # update_fig_layout(fig)
    fig.update_layout(
        {
            "title": "Click to select a timestep of interest",
            "title_font_color": "white",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "legend_font_color": "white",
            "legend_title": "Muscle",
            "legend_title_font_color": "white",
        }
    )
    fig.update_xaxes(
        {
            "color": "white",
            "showgrid": False,
            "ticks": "outside",
            "title": "timestep",
        }
    )
    fig.update_yaxes(
        {
            "color": "white",
            "gridcolor": "grey",
            "ticks": "outside",
            "title": "Force",
        }
    )

    return fig


def click_visual_toi_selector(df):
    fig = visual_toi_selector(df)
    selected_points = plotly_events(
        fig, click_event=True, hover_event=False, select_event=False
    )
    if selected_points:
        st.session_state.toi = selected_points[0]["x"]
        st.rerun()


def visual_toi_boi_force_vectors(
    mesh_path,
    muscle_force_path,
    force_origins_path,
    force_vectors_path,
    step,
):
    mesh = pv.read(os.path.join(mesh_path))
    df, _ = read_input(muscle_force_path)

    force_origins = pd.read_json(force_origins_path, orient="records", lines=True)
    force_vectors = pd.read_json(force_vectors_path, orient="records", lines=True)

    pl = pv.Plotter(off_screen=False)
    pl.view_xy()
    pl.camera.zoom(2.5)
    pl.background_color = "black"
    pl.add_axes(interactive=True)
    text = pl.add_text(f"Timestep: {step}", color="white")

    pl.add_mesh(mesh, color="white")

    muscle_names = [name for name in force_vectors.keys() if name != "time"]

    force_vector_actor = {}

    scale_factor = 0.01
    for muscle in muscle_names:
        for map in st.session_state.color_map:
            if muscle in map:
                rgb_color = st.session_state.color_map[map]
        color = [int(color) for color in re.findall(r"\d+", rgb_color)]

        pl.add_mesh(
            pv.PolyData(force_origins[muscle][step]),
            color=color,
            point_size=10,
            render_points_as_spheres=True,
        )
        force_vector_actor[muscle] = pl.add_mesh(
            pv.Arrow(
                start=force_origins[muscle][step],
                direction=force_vectors[muscle][step],
                scale=df[f"/forceset/{muscle}|active_fiber_force"][step] * scale_factor,
            ),
            color=color,
        )
    stpyvista(pl, key="toiboi")
