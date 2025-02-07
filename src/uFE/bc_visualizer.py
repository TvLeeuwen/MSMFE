"""

"""
# Imports ---------------------------------------------------------------------
import argparse
import numpy as np
import pyvista as pv


# Defs ------------------------------------------------------------------------
def parse_arguments():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Manually select boundary conditions for a .mesh file",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help='Use switches followed by "=" to use CLI file autocomplete, example "-i="',
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Input path to .mesh file",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--dirichlet",
        type=str,
        help="Path to dirichlet boundary conditions",
        required=False,
    )
    parser.add_argument(
        "-n",
        "--neumann",
        type=str,
        help="Path to neumann boundary conditions",
        required=False,
    )
    return parser.parse_args()


# Main ------------------------------------------------------------------------
def visualize_BCs(
    mesh_path,
    dirichlet_path=None,
    neumann_path=None,
):
    mesh = pv.read(mesh_path)
    print("-- Mesh vertex, element count:", mesh.n_points, mesh.n_cells)

    pl = pv.Plotter()
    pl.add_mesh(mesh, show_edges=True, color="white")
    pl.view_xz()
    pl.camera.up = (0, 0, -1)
    # pl.camera.zoom(2.5)
    pl.background_color = "white"
    pl.add_text(
        "Press 'q' to quit",
        color="white",
        position="lower_edge",
    )
    pl.add_axes(interactive=True)

    if dirichlet_path:
        mesh_dirichlet = pv.PolyData(np.load(dirichlet_path, allow_pickle=True))
        print(" - Dirichlet vertex count:", mesh_dirichlet.n_points)
        pl.add_mesh(mesh_dirichlet.points, color="blue")
    if neumann_path:
        mesh_neumann = pv.PolyData(np.load(neumann_path, allow_pickle=True))
        print(" - Neumann vertex count:", mesh_neumann.n_points)
        pl.add_mesh(mesh_neumann.points, color="red")
    # stpyvista(pl, key="bcs")
    pl.show(auto_close=True)


if __name__ == "__main__":
    args = parse_arguments()

    visualize_BCs(
        args.input,
        args.dirichlet,
        args.neumann,
    )
