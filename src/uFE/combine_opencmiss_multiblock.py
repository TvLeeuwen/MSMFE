"""
"""
# Imports ---------------------------------------------------------------------
import os
import sys
import glob
import argparse
import pyvista as pv
import visualize_opencmiss
from utils.formatting import return_timer, print_section


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
        help="Path/to/mesh to be visualized",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output filename ()",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
@return_timer
def combine_OpenCMISS_blocks(
    solution_path: str,
    combined_solution_path: str | None = None,
    visuals: bool = False,
):
    print_section()
    print("-- Initiating mesh combination, combining blocks:")

    input_files = sorted(glob.glob(f"{solution_path}*.vtK"))

    multi_block = pv.MultiBlock()

    for i, block_file in enumerate(input_files):
        mesh = pv.read(block_file)
        print(f" - {os.path.basename(block_file)}, cells: {mesh.n_cells}")
        multi_block.append(mesh)
        multi_block.set_block_name(i, block_file.split("/")[-1])

    mesh = multi_block.combine()
    print(f"-- Mesh combined, total number of cells: {mesh.n_cells}")

    mesh.save(combined_solution_path, binary=False)
    print(f" - Writing files:\n - {combined_solution_path}\n - time elapsed:")

    if visuals:
        pl = pv.Plotter()
        pl.add_text(os.path.basename(combined_solution_path))
        pl.add_mesh(
            mesh,
            scalars="Structure",
            cmap="bone",
        )
        pl.view_xz()
        pl.add_axes(interactive=True)
        pl.camera.up = (0, 0, -1)

        pl.show()


### Main -----------------------------------------------------------------------
if __name__ == "__main__":
    args = parse_arguments()

    combine_OpenCMISS_blocks(
        args.input,
        args.output,
        args.visuals,
    )
