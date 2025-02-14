"""
Visualize OpenCMISS results by calling `visualize_OpenCMISS_results()`
@params
:param `result_file`: /Path/to/input/mesh.mesh
:(optional) param `result_metric`: color map scalar for the result mesh, metric choices below:
:(optional) param `initial_file`: /Path/to/input/mesh.mesh
:(optional) param `initial_metric`: color map scalar for the initial mesh, metric choices from:
::  default=None
:: "Displacement"
:: "Stress"
:: "Strain"
:: "Elastic work"
@returns: Void
@outputs: Visual plot of modelled object with chosen metric colormap
"""

### Imports --------------------------------------------------------------------
import os
import sys
import glob
import argparse
from pathlib import Path
import pyvista as pv


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
        help="Path/to/mesh to be visualized",
        required=True,
    )
    # metric_choices = ["displacement"]
    parser.add_argument(
        "-im",
        "--imetric",
        help="Output metric to be visualized on the resulting mesh",
        # type=str_lowercase,
        # choices=metric_choices,
        default=None,
    )
    parser.add_argument(
        "-c",
        "--compare",
        type=str,
        help="Path/to/file`.vtk` to be visualized in comparison to main input",
    )
    parser.add_argument(
        "-cm",
        "--cmetric",
        help="Output metric to be visualized on the comparing mesh",
        # type=str_lowercase,
        # choices=metric_choices,
        default=None,
    )

    return parser.parse_args()


def str_lowercase(s: str) -> str:
    return s.lower()


def visualize_OpenCMISS_results(
    result_file: Path,
    result_metric: str = None,
    initial_file: Path = None,
    initial_metric: str = None,
) -> None:
    """
    Visualize OpenCMISS results
    @params
    :param `result_file`: /Path/to/input/mesh.mesh
    :(optional) param `result_metric`: color map scalar for the result mesh, metric choices below:
    :(optional) param `initial_file`: /Path/to/input/mesh.mesh
    :(optional) param `initial_metric`: color map scalar for the initial mesh, metric choices from:
    ::  default=None
    :: "Displacement"
    :: "Stress"
    :: "Strain"
    :: "Elastic work"
    @returns: Void
    @outputs: Visual plot of modelled object with chosen metric colormap
    """

    vtk_files = sorted(glob.glob(f"{result_file}/*.vtk"))  # Adjust the path

    multi_block = pv.MultiBlock()

    for i, vtk_file in enumerate(vtk_files):
        mesh = pv.read(vtk_file)
        multi_block.append(mesh)  # Add to MultiBlock

        # Optionally, name each block (e.g., using the filename)
        multi_block.set_block_name(i, vtk_file.split("/")[-1])

    # -------------------------------------------------------------------------

    # mesh = pv.read(result_file)
    # mesh = mesh.threshold(value=1, scalars="Structure", invert=False)

    pl = pv.Plotter()
    # pl.add_text(os.path.basename(result_file))
    pl.add_text(vtk_files[-1])
    for i, block in enumerate(multi_block):
        if isinstance(block, pv.DataSet):
            half_mesh = block.clip('y',
                                   crinkle=True,)
            thresholded = half_mesh.threshold(
                value=1,
                scalars="Structure",
                invert=False,
            )
            pl.add_mesh(
                thresholded,
                scalars="Structure",
                cmap="reds",
            )
    pl.view_xz()
    pl.camera.up = (0, 0, -1)

    # pl.add_mesh(
    #     mesh,
    #     color="white",
    #     lighting=True,
    #     scalars=result_metric,
    #     cmap="reds",
    # )

    # if initial_file:
    #     initial_mesh = pv.read(initial_file)
    #     pl.add_mesh(
    #         initial_mesh,
    #         color="white",
    #         lighting=True,
    #         scalars=initial_metric,
    #         cmap="coolwarm",
    #     )
    pl.show()


### Main -----------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_arguments()

    visualize_OpenCMISS_results(
        args.input,
        args.imetric,
        args.compare,
        args.cmetric,
    )
