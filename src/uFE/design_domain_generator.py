"""
Generates design domain for the supplied mesh.
Design domain in OpenCMISS are nodal values either set to bone (1), non-bone(0) or
immutable bone(-1). The default value within OpenCMISS is 1. Currently, this
script allows for the automatic setting of an immutable surface mesh, retaining
the bone's original shape during adaptation.

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

    return parser.parse_args()


def write_design_domain(
    design_path,
    design_selection,
):
    df = pd.DataFrame(
        0,
        index=range(len(design_selection.points)),
        columns=["design_nodes", "design_domain"],
    )
    df["design_nodes"] = design_selection.point_data["vtkOriginalPointIds"]
    df["design_domain"] = -1

    pd.DataFrame(df).to_json(design_path, orient="records", lines=True)

    print(f"-- Writing files:\n - {design_path}")

    return design_path


# Main ------------------------------------------------------------------------
def generate_design_domain(
    mesh_path,
    output_path,
    visuals=False,
):
    print_section()

    print(f"-- Generating design domain - loading file:\n - {mesh_path}")

    mesh = pv.read(mesh_path)
    surf = mesh.extract_surface()

    write_design_domain(
        output_path,
        surf,
    )

    if visuals:
        pl = pv.Plotter()
        pl.add_mesh(
            mesh,
            color="white",
            scalars=None,
        )
        pl.add_mesh(surf.points, color="green")
        pl.show()


if __name__ == "__main__":
    args = parse_arguments()

    generate_design_domain(
        args.input,
        args.output,
    )
