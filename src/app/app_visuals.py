"""Definitions for data visualization in streamlit"""

# Imports ---------------------------------------------------------------------
import os
import time
import multiprocessing
import streamlit as st
import plotly.colors as pc
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from src.MSM.sto_generator import read_input
from src.MSM.generate_force_vector_gif import generate_vector_gif


# Defs ------------------------------------------------------------------------
def visual_compare_timeseries(sto1, sto2):
    df, _ = read_input(sto1)
    df2, _ = read_input(sto2)

    fig = go.Figure()

    color_scale = [hex[1] for hex in pc.get_colorscale("Viridis")]

    for column in df.columns:
        if column != "time":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color_scale[2]),
                    name=f"Input: {column}",
                    legendgroup=column,
                )
            )

    for column in df2.columns:
        if column != "time":
            fig.add_trace(
                go.Scatter(
                    x=df2.index,
                    y=df2[column],
                    mode="lines",
                    line=dict(color=color_scale[-3]),
                    name=f"Output: {column}",
                    legendgroup=column,
                )
            )

    fig.update_layout(
        # title=f"{os.path.basename(sto1)}\n versus\n{os.path.basename(sto2)}",
        height=1000,
        xaxis_title="Time (s)",
        yaxis_title="Value",
        legend_title="Variables",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="right",
            x=0.5,
            itemsizing="constant",
            traceorder="grouped",
        ),
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def visual_validate_muscle_parameters(sto1):
    df, _ = read_input(sto1)

    # Required for a consistent color index
    columns = set()
    for column in df.columns:
        if column != "time":
            columns.add(column.split("|")[0])
    colors = px.colors.sample_colorscale("viridis", [n/(len(columns)-1) for n in range(len(columns))])
    color_map = {col: colors[i] for i, col in enumerate(columns)}

    fig = go.Figure()
    for column in df.columns:
        if column != "time":
            state_name = column.split("|")[1]
            muscle = column.split("|")[0]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color_map[muscle]),
                    name=column,
                    legendgroup=state_name,
                )
            )

    fig.update_layout(
        height=1000,
        xaxis_title="Time (s)",
        yaxis_title="Value",
        legend_title="Variables",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="right",
            x=0.5,
            itemsizing="constant",
            traceorder="grouped",
        ),
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def visual_force_vector_gif(
    mesh_file,
    moco_solution_path,
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
            moco_solution_path,
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

