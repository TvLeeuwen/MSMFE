""" 
Select the location of both Dirichlet and Neumann boundary conditions manually by calling `assign_BCs_manually()`
@params
:param `mesh_path`: /Path/to/input/mesh.mesh
:(optional) param `surf_select`: bool, allows for selection of surface nodes only when True.
:: Only when supported by mesh type, i.e. mmg level-set generated .mesh. `Default=False`.
:(optional) param `txt`: bool, allows for the output of human readible txt files.
@output:
:file `input_file_dirichlet_BC.npy` list of selected nodes where displacement is constrained
:file `input_file_neumann_BC.npy` list of selected nodes where force is applied
:(optional) file `input_file_dirichlet_BC.txt` list of selected nodes where displacement is constrained
:(optional) file `input_file_neumann_BC.txt` list of selected nodes where force is applied
"""

### Imports --------------------------------------------------------------------
import os
import argparse
import multiprocessing
from pathlib import Path
import pyvista as pv
import streamlit as st
from stpyvista import stpyvista
import numpy as np

from src.uFE.utils.handle_args import ask_user_to_continue
from src.uFE.utils.formatting import timer, print_section


### Defs -----------------------------------------------------------------------
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
        "-s",
        "--surface",
        action="store_true",
        help="Enable to select surface nodes only",
    )
    parser.add_argument(
        "-t",
        "--txt",
        action="store_true",
        help="Enable human readable output (.txt)",
    )

    return parser.parse_args()


def handle_args_surf_select(mesh, surf_select):
    if surf_select:
        ### Extract surface cells for boundary condition selection - region 10
        select_cells = np.array([]).astype(int)
        for i, c in enumerate(mesh.cell_data["medit:ref"]):
            if c == 10:
                select_cells = np.append(select_cells, i)
        print(select_cells)
        if select_cells:
            mesh = mesh.extract_cells(select_cells)
        else:
            print("- No distinct surface domain found - assigning BCs volumetricly")
            mesh.extract_cells(mesh.cells)
    else:
        mesh.extract_cells(mesh.cells)

    return mesh


def pick_bcs(mesh, msg: str = ""):
    bc_selection_plotter = pv.Plotter()
    bc_selection_plotter.add_mesh(mesh, show_edges=True, color="white")
    bc_selection_plotter.enable_cell_picking(mesh, show_message=False)
    bc_selection_plotter.add_text(
        "\n" + msg,
        color="white",
        position="upper_edge",
    )
    bc_selection_plotter.add_text(
        "Use 'r' to select cells \n Press 'q' or 'e' to continue",
        color="white",
        position="lower_edge",
    )
    bc_selection_plotter.set_background("black")
    bc_selection_plotter.show()

    if bc_selection_plotter.picked_cells:
        bc_plotter = pv.Plotter()
        bc_plotter.add_mesh(
            bc_selection_plotter.picked_cells, color="white", show_edges=True
        )
        bc_plotter.set_background("black")
        bc_plotter.add_text(
            "\n Selected elements",
            color="white",
            position="upper_edge",
        )
        bc_plotter.add_text(
            "Press 'q' to continue",
            color="white",
            position="lower_edge",
        )
        bc_plotter.show()

        return bc_selection_plotter.picked_cells
    return None


def set_bcs(
    mesh_path,
    output_path,
    txt,
):
    mesh = pv.read(mesh_path)

    dirichlet_selection = pick_bcs(mesh, "Select constrained boundary elements")
    neumann_selection = pick_bcs(mesh, "Select loaded boundary elements")

    dirichlet_path, neumann_path = write_output(
        mesh_path,
        output_path,
        dirichlet_selection,
        neumann_selection,
        txt,
    )

    return dirichlet_path, neumann_path


def write_output(
    mesh_path,
    output_base,
    dirichlet_selection,
    neumann_selection=None,
    txt=False,
):
    dirichlet_path, neumann_path = None, None
    if dirichlet_selection:
        dirichlet_path = output_base + "_manual_dirichlet_BC.npy"
        if neumann_selection:
            neumann_path = output_base + "_manual_neumann_BC.npy"
            np.save(
                neumann_path,
                neumann_selection.points,
            )

        np.save(
            dirichlet_path,
            dirichlet_selection.points,
        )
        print(f"-- Writing files:")
        print(f" - {dirichlet_path}\n - {neumann_path}") if neumann_path else print(
            f" - {dirichlet_path}"
        )

    # if txt:
    #     print(f" - {mesh_path.name.replace('.mesh', '_dirichlet_BC.txt')}")
    #     print(f" - {mesh_path.name.replace('.mesh', '_neumann_BC.txt')}")

    return dirichlet_path, neumann_path


def visualize_BCs(
    mesh_path,
    dirichlet_path=None,
    neumann_path=None,
):
    mesh = pv.read(mesh_path)
    pl = pv.Plotter()
    pl.add_mesh(mesh, show_edges=True, color="white")
    pl.view_xy()
    # pl.camera.zoom(2.5)
    pl.background_color = "black"
    pl.add_text(
        "Press 'q' to quit",
        color="white",
        position="lower_edge",
    )
    pl.add_axes(interactive=True)

    if dirichlet_path:
        mesh_dirichlet = pv.PolyData(np.load(dirichlet_path, allow_pickle=True))
        pl.add_mesh(mesh_dirichlet.points, color="blue")
    if neumann_path:
        mesh_neumann = pv.PolyData(np.load(neumann_path, allow_pickle=True))
        pl.add_mesh(mesh_neumann.points, color="red")
    # stpyvista(pl, key="bcs")
    pl.show(auto_close=True)


### Main ----------------------------------------------------------------------
def assign_bcs_manually(
    mesh_path,
    output_base,
    queue,
    surf_select=False,
    txt=False,
):
    """
    Select the location of both Dirichlet and Neumann boundary conditions manually
    @params
    :param `mesh_path`: /Path/to/input/mesh.mesh
    :(optional) param `surf_select`: bool, allows for selection of surface nodes only when True.
    :: Only when supported by mesh type, i.e. mmg level-set generated .mesh. `Default=False`.
    :(optional) param `txt`: bool, allows for the output of human readible txt files.
    @returns: void
    @outputs:
    :file `input_file_dirichlet_BC.npy` list of selected nodes where displacement is constrained
    :file `input_file_neumann_BC.npy` list of selected nodes where force is applied
    :(optional) file `input_file_dirichlet_BC.txt` list of selected nodes where displacement is constrained
    :(optional) file `input_file_neumann_BC.txt` list of selected nodes where force is applied
    """
    print_section()

    print(
        f"-- Manual boundary condition picker initiated - loading file:\n - {mesh_path}"
    )
    # if os.path.splitext(mesh_path)[1] != ".mesh":
    #     if os.path.exists(mesh_path):
    #         print("DEBUG",mesh_path)
    #         mesh = meshio.read(mesh_path)
    #         mesh_path = os.path.splitext(mesh_path)[0] + ".mesh"
    #         print(mesh_path)
    #         meshio.write(mesh_path, mesh)

    #
    # if surf_select:
    #     mesh = handle_args_surf_select(mesh, surf_select)

    dirichlet_path, neumann_path = set_bcs(
        mesh_path,
        output_base,
        txt,
    )

    queue.put([dirichlet_path, neumann_path])


if __name__ == "__main__":
    args = parse_arguments()

    assign_bcs_manually(Path(args.input), surf_select=args.surface, txt=args.txt)
