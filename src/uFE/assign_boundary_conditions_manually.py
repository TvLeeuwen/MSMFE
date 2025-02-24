"""
Select the location of both Dirichlet and Neumann boundary conditions manually by calling `assign_BCs_manually()`
@params
:param `mesh_path`: /Path/to/input/mesh.mesh
:(optional) param `surf_select`: bool, allows for selection of surface nodes only when True.
:: Only when supported by mesh type, i.e. mmg level-set generated .mesh. `Default=False`.
@output:
:file `input_file_dirichlet_BC.npy` list of selected nodes where displacement is constrained
:file `input_file_neumann_BC.npy` list of selected nodes where force is applied
"""

# Imports ---------------------------------------------------------------------
import os
import sys
import argparse
import numpy as np
import pandas as pd
import pyvista as pv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from src.uFE.utils.formatting import timer, print_section
from src.uFE.bc_visualizer import visualize_BCs


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
        "-o",
        "--output",
        type=str,
        help="Output base name for BC files",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--surface",
        action="store_true",
        help="Enable to select surface nodes only",
    )

    return parser.parse_args()


def handle_args_surf_select(mesh, surf_select):
    """
    Extract surface cells for boundary condition selection - region 10

    :param mesh [TODO:type]: [TODO:description]
    :param surf_select [TODO:type]: [TODO:description]
    """
    if surf_select:
        select_cells = np.array([]).astype(int)
        for i, c in enumerate(mesh.cell_data["medit:ref"]):
            if c == 10:
                select_cells = np.append(select_cells, i)
        if select_cells.any():
            mesh = mesh.extract_cells(select_cells)
        else:
            print("- No distinct surface domain found - assigning BCs volumetricly")
            mesh.extract_cells(mesh.cells)
    else:
        mesh.extract_cells(mesh.cells)

    return mesh


def pick_bcs(mesh, msg: str = ""):
    bc_select_pl = pv.Plotter()
    bc_select_pl.add_mesh(mesh, show_edges=True, color="white")
    bc_select_pl.enable_cell_picking(mesh, show_message=False)
    bc_select_pl.add_text(
        "\n" + msg,
        color="black",
        position="upper_edge",
    )
    bc_select_pl.add_text(
        "Use 'r' to select cells \n Press 'q' or 'e' to continue",
        color="black",
        position="lower_edge",
    )
    bc_select_pl.set_background("white")
    bc_select_pl.view_xz()
    bc_select_pl.camera.up = (0, 0, -1)
    bc_select_pl.show()

    if bc_select_pl.picked_cells:
        bc_pl = pv.Plotter()
        bc_pl.add_mesh(bc_select_pl.picked_cells, color="white", show_edges=True)
        bc_pl.set_background("white")
        bc_pl.add_text(
            "\n Selected elements",
            color="black",
            position="upper_edge",
        )
        bc_pl.add_text(
            "Press 'q' to continue",
            color="black",
            position="lower_edge",
        )
        bc_pl.view_xz()
        bc_pl.camera.up = (0, 0, -1)
        bc_pl.show()

        return bc_select_pl.picked_cells
    return None


def set_bcs(
    mesh_path,
    output_path,
    surf_select,
):
    mesh = pv.read(mesh_path)

    mesh = handle_args_surf_select(mesh, surf_select)

    dirichlet_selection = pick_bcs(mesh, "Select constrained boundary elements")
    neumann_selection = pick_bcs(mesh, "Select loaded boundary elements")

    dirichlet_path, neumann_path = write_output(
        output_path,
        dirichlet_selection,
        neumann_selection,
    )

    return dirichlet_path, neumann_path


def write_output(
    output_base,
    dirichlet_selection,
    neumann_selection=None,
):
    dirichlet_path, neumann_path = None, None



    if dirichlet_selection:
        dirichlet_path = output_base + "_manual_dirichlet_BC.json"
        df = pd.DataFrame(
            0,
            index=range(len(dirichlet_selection.points)),
            columns=["dirichlet_nodes", "dirichlet_value"],
        )
        df["dirichlet_nodes"] = dirichlet_selection.point_data["vtkOriginalPointIds"]

        if neumann_selection:
            neumann_path = output_base + "_manual_neumann_BC.json"
            df2 = pd.DataFrame(
                0,
                index=range(len(neumann_selection.points)),
                columns=["neumann_nodes", "neumann_x", "neumann_y", "neumann_z"],
            )
            df2["neumann_nodes"] = neumann_selection.point_data["vtkOriginalPointIds"]
            df2["neumann_y"] = -1

            pd.DataFrame(df2).to_json(neumann_path, orient="records", lines=True)

        pd.DataFrame(df).to_json(dirichlet_path, orient="records", lines=True)

        print(f"-- Writing files:")
        print(f" - {dirichlet_path}\n - {neumann_path}") if neumann_path else print(
            f" - {dirichlet_path}"
        )

    return dirichlet_path, neumann_path


# Main ------------------------------------------------------------------------
def assign_bcs_manually(
    mesh_path,
    output_base,
    surf_select=False,
):
    """
    Select the location of both Dirichlet and Neumann boundary conditions manually
    @params
    :param `mesh_path`: /Path/to/input/mesh.mesh
    :(optional) param `surf_select`: bool, allows for selection of surface nodes only when True.
    :: Only when supported by mesh type, i.e. mmg level-set generated .mesh. `Default=False`.
    @returns: void
    @outputs:
    :file `input_file_dirichlet_BC.npy` list of selected nodes where displacement is constrained
    :file `input_file_neumann_BC.npy` list of selected nodes where force is applied
    """
    print_section()

    print(
        f"-- Manual boundary condition picker initiated - loading file:\n - {mesh_path}"
    )
    print(output_base)

    dirichlet_path, neumann_path = set_bcs(
        mesh_path,
        output_base,
        surf_select,
    )

    visualize_BCs(mesh_path, dirichlet_path, neumann_path)


if __name__ == "__main__":
    args = parse_arguments()

    assign_bcs_manually(
        args.input,
        args.output,
        args.surface,
    )
