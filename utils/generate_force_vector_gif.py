import os
import numpy as np
import pandas as pd
import pyvista as pv
import matplotlib.pyplot as plt

from src.MSM.sto_generator import read_input


def generate_vector_gif(
    mesh_path,
    solution_path,
    force_origins_path,
    force_vectors_path,
    gif_path,
):
    mesh = pv.read(os.path.join(mesh_path))
    df, _ = read_input(solution_path)

    force_origins = pd.read_json(force_origins_path, orient='records', lines=True)
    force_vectors = pd.read_json(force_vectors_path, orient='records', lines=True)

    # Initiate plotter
    pl = pv.Plotter(off_screen=False)
    pl.view_xy()
    pl.camera.zoom(2.5)
    pl.background_color = "black"
    pl.add_axes(interactive=True)

    pl.add_mesh(mesh, color="white")

    muscle_names = [name for name in force_vectors.keys() if name != 'time']
    colors = plt.cm.gist_rainbow(np.linspace(0, 1, len(muscle_names)))

    force_vector_actor = {}
    for muscle, color in zip(muscle_names, colors):
        rgb_color = color[:3]

        pl.add_mesh(
            pv.PolyData(force_origins[muscle][0]),
            color="blue",
            point_size=30,
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

    pl.open_gif(gif_path)
    # Generate steps and animation behaviour
    for step, force in enumerate(df["/forceset/FL_p_test/normalized_tendon_force"]):
        if step % 5 == 0:
            print(f"Generating gif: {step} / {len(df['time'])}", end="\r")
            for muscle in muscle_names:
                force_vector_actor[muscle].scale = force
                # force_vector_actor[muscle].scale = [.3,.3,.3]
                force_vector_actor[muscle].position = force_origins[muscle][step]
                force_vector_actor[muscle].orientation =force_vectors[muscle][step]
            pl.write_frame()
    pl.close()

    print("\nGif succesfully generated.")
