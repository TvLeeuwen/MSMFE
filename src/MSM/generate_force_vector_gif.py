import os
import re
import numpy as np
import pandas as pd
import pyvista as pv
import streamlit as st
import plotly.express as px
from stpyvista import stpyvista
import matplotlib.pyplot as plt

from src.MSM.sto_generator import read_input


def generate_vector_gif(
    mesh_path,
    muscle_force_path,
    force_origins_path,
    force_vectors_path,
    gif_path,
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
    text = pl.add_text(f"Timestep: 0", color="white")

    pl.add_mesh(mesh, color="white")

    muscle_names = [name for name in force_vectors.keys() if name != "time"]
    colors = plt.cm.gist_rainbow(np.linspace(0, 1, len(muscle_names)))

    force_vector_actor = {}
    legend = []
    for muscle, color in zip(muscle_names, colors):
        rgb_color = color[:3]

        pl.add_mesh(
            pv.PolyData(force_origins[muscle][0]),
            color="blue",
            point_size=20,
            render_points_as_spheres=True,
        )
        force_vector_actor[muscle] = pl.add_mesh(
            pv.Arrow(
                start=force_origins[muscle][0],
                direction=force_vectors[muscle][0],
                scale=0.1,
            ),
            color=rgb_color,
        )
        legend.append([muscle, rgb_color])
    pl.add_legend(legend)

    pl.open_gif(gif_path)
    # Generate steps and animation behaviour
    scale_factor = 0.01
    for step, time in enumerate(df["time"]):
        if step % 5 == 0:
            print(f"Generating gif: {step} / {len(df['time'])}", end="\r")
            pl.remove_actor(text)
            text = pl.add_text(f"Step: {step}, time={time:.2f}", color="white")
            for muscle in muscle_names:
                force_vector_actor[muscle].scale = (
                    df[
                        # f"/forceset/{muscle}/normalized_tendon_force"
                        f"/forceset/{muscle}|active_fiber_force"
                    ][step]
                    * scale_factor
                )
                force_vector_actor[muscle].position = force_origins[muscle][step]
                force_vector_actor[muscle].orientation = force_vectors[muscle][step]
            pl.write_frame()
    pl.close()

    print("\nGif succesfully generated.")


def generate_force_vectors(
    mesh_path,
    muscle_force_path,
    force_origins_path,
    force_vectors_path,
    step,
    # scale_factor,
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
        color = [int(color) for color in re.findall(r'\d+', rgb_color)]

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
