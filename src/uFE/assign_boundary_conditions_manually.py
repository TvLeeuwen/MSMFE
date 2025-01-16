""" 
Select the location of both Dirichlet and Neumann boundary conditions manually by calling `assign_BCs_manually()`
@params
:param `input_file`: /Path/to/input/mesh.mesh
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
import sys
import argparse
from pathlib import Path
import pyvista as pv
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))
from utils.handle_args import ask_user_to_continue
from utils.formatting import timer, print_section


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
    bc_selection = None
    while bc_selection == None:
        bc_selection_plotter = pv.Plotter()
        bc_selection_plotter.add_mesh(mesh, show_edges=True, color="white")
        bc_selection_plotter.enable_cell_picking(mesh, show_message=False)
        bc_selection_plotter.add_text("\n" + msg, position="upper_edge")
        bc_selection_plotter.add_text(
            "Use 'r' to select cells, after, press 'q' to continue", position="lower_edge"
        )
        bc_selection_plotter.set_background("white")
        bc_selection_plotter.show()

        bc_selection = bc_selection_plotter.picked_cells

    bc_plotter = pv.Plotter()
    bc_plotter.add_mesh(bc_selection, color="white", show_edges=True)
    bc_plotter.add_text("\n Selected elements", position="upper_edge")
    bc_plotter.add_text(
        "Press 'q' to continue", position="lower_edge"
    )
    bc_plotter.show()

    if not ask_user_to_continue("Continue with selected elements? (y/n): "):
        bc_selection = pick_bcs(mesh, msg=msg)

    return bc_selection


def set_bcs(mesh):
    dirichlet_selection = pick_bcs(mesh, "Select constrained boundary elements")
    neumann_selection = pick_bcs(mesh, "Select loaded boundary elements")

    bc_plotter = pv.Plotter()
    bc_plotter.add_mesh(mesh, show_edges=True, color="white", scalars=None)
    bc_plotter.add_mesh(dirichlet_selection.points, color="blue")
    bc_plotter.add_mesh(neumann_selection.points, color="red")
    bc_plotter.show()

    if not ask_user_to_continue("Write selected boundary nodes? (y/n): "):
        dirichlet_selection, neumann_selection = set_bcs(mesh)

    return dirichlet_selection, neumann_selection


def write_output(input_file, dirichlet_selection, neumann_selection, txt=False):
    np.save(
        input_file.parents[0] / input_file.name.replace(".mesh", "_neumann_BC.npy"),
        neumann_selection.point_data["vtkOriginalPointIds"],
    )
    np.save(
        input_file.parents[0] / input_file.name.replace(".mesh", "_dirichlet_BC.npy"),
        dirichlet_selection.point_data["vtkOriginalPointIds"],
    )
    if txt:
        np.savetxt(
            input_file.parents[0] / input_file.name.replace(".mesh", "_neumann_BC.txt"),
            neumann_selection.point_data["vtkOriginalPointIds"],
            delimiter=",",
        )
        np.savetxt(
            input_file.parents[0] / input_file.name.replace(".mesh", "_dirichlet_BC.txt"),
            dirichlet_selection.point_data["vtkOriginalPointIds"],
            delimiter=",",
        )

    print(f"-- Writing files:")
    print(f" - {input_file.name.replace('.mesh', '_dirichlet_BC.npy')}")
    print(f" - {input_file.name.replace('.mesh', '_neumann_BC.npy')}")
    if txt:
        print(f" - {input_file.name.replace('.mesh', '_dirichlet_BC.txt')}")
        print(f" - {input_file.name.replace('.mesh', '_neumann_BC.txt')}")

### Main ----------------------------------------------------------------------
@timer
def assign_bcs_manually(input_file: Path, surf_select=False, txt=False) -> None:
    """
    Select the location of both Dirichlet and Neumann boundary conditions manually
    @params
    :param `input_file`: /Path/to/input/mesh.mesh
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
        f"-- Manual boundary condition picker initiated - loading file:\n - {input_file.name}"
    )

    with input_file.open("r"):
        mesh = pv.read(input_file)

    mesh = handle_args_surf_select(mesh, surf_select)

    dirichlet_selection, neumann_selection = set_bcs(mesh)

    write_output(input_file, dirichlet_selection, neumann_selection, txt)

    print("-- Boundary conditions assigned, total time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    assign_bcs_manually(Path(args.input), surf_select=args.surface, txt=args.txt)
