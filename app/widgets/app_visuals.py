"""Definitions for data visualization in streamlit"""

# Imports ---------------------------------------------------------------------
import os
import time
import multiprocessing
import streamlit as st
import plotly.colors as pc
import plotly.graph_objects as go

from src.sto_generator import read_input
from utils.generate_force_vector_gif import generate_vector_gif


# Defs ------------------------------------------------------------------------
def visual_compare_timeseries(sto1, sto2):
    df, _ = read_input(sto1)
    df2, _ = read_input(sto2)

    color_scale_df = pc.get_colorscale("Viridis")
    fig = go.Figure()
    for i, column in enumerate(df.columns):
        if column != "time":
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color_scale_df[i % len(color_scale_df)][1]),
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

    color_scale_df = pc.get_colorscale("Viridis")
    fig = go.Figure()
    for i, column in enumerate(df.columns):
        if (
            column != "time"
        ):
            state_name = column.split('|')[1]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[column],
                    mode="lines",
                    line=dict(color=color_scale_df[i % len(color_scale_df)][1]),
                    name=column,
                    # legendgroup=column,
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
    # TODO - change to model_solution_vectors.gif
    st.session_state.gif_path = os.path.join(output_path, "force_vectors.gif")

    # TODO - make geom dynamic: mesh file
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
