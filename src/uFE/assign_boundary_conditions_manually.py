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
import sys
import argparse
from pathlib import Path
import pyvista as pv
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[2]))
from src.uFE.utils.formatting import timer, print_section
from src.uFE.bc_visualizer import visualize_BCs


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
    parser.add_argument(
        "-t",
        "--txt",
        action="store_true",
        help="Enable human readable output (.txt)",
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
    txt,
):
    mesh = pv.read(mesh_path)

    mesh = handle_args_surf_select(mesh, surf_select)

    dirichlet_selection = pick_bcs(mesh, "Select constrained boundary elements")
    neumann_selection = pick_bcs(mesh, "Select loaded boundary elements")

    if neumann_selection:
        pass


    dirichlet_path, neumann_path = write_output(
        output_path,
        dirichlet_selection,
        neumann_selection,
        txt,
    )

    return dirichlet_path, neumann_path


def write_output(
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
            if txt:
                np.savetxt(
                    os.path.splitext(neumann_path)[0] + ".txt",
                    dirichlet_selection.points,
                    delimiter=",",
                )

        np.save(
            dirichlet_path,
            dirichlet_selection.points,
        )
        if txt:
            np.savetxt(
                os.path.splitext(dirichlet_path)[0] + ".txt",
                dirichlet_selection.points,
                delimiter=",",
            )
        print(f"-- Writing files:")
        print(f" - {dirichlet_path}\n - {neumann_path}") if neumann_path else print(
            f" - {dirichlet_path}"
        )
        if txt:
            print(
                f" - {os.path.splitext(dirichlet_path)[0] + '.txt'}\
                \n - {os.path.splitext(neumann_path)[0] + '.txt'}"
            ) if neumann_path else print(
                f" - {os.path.splitext(dirichlet_path)[0] + '.txt'}"
            )

    return dirichlet_path, neumann_path


# Main ------------------------------------------------------------------------
def assign_bcs_manually(
    mesh_path,
    output_base,
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

    print(txt)
    dirichlet_path, neumann_path = set_bcs(
        mesh_path,
        output_base,
        surf_select,
        txt,
    )

    visualize_BCs(mesh_path, dirichlet_path, neumann_path)


if __name__ == "__main__":
    args = parse_arguments()

    assign_bcs_manually(
        args.input,
        args.output,
        args.surface,
        args.txt,
    )
