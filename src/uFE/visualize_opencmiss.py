"""
Visualize OpenCMISS results by calling `visualize_OpenCMISS_results()`
@params
:param `opencmiss_solution_path`: /Path/to/input/mesh.mesh
:(optional) param `solution_metric`: color map scalar for the result mesh, metric choices below:
:(optional) param `initial_path`: /Path/to/input/mesh.mesh
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
    parser.add_argument(
        "-im",
        "--imetric",
        help="Output metric to be visualized on the resulting mesh",
        # type=str_lowercase,
        # choices=metric_choices,
        default="Structure",
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
    opencmiss_solution_path: str,
    solution_metric: str = "Structure",
    compare_path: str | None = None,
    compare_metric: str | None = None,
) -> None:
    """
    Visualize OpenCMISS results
    @params
    :param `opencmiss_solution_path`: /Path/to/input/mesh.mesh
    :(optional) param `solution_metric`: color map scalar for the result mesh, metric choices below:
    :(optional) param `initial_path`: /Path/to/input/mesh.mesh
    :(optional) param `initial_metric`: color map scalar for the initial mesh, metric choices from:
    ::  default=None
    :: "Displacement"
    :: "Stress"
    :: "Strain"
    :: "Elastic work"
    @returns: Void
    @outputs: Visual plot of modelled object with chosen metric colormap
    """

    # -------------------------------------------------------------------------

    mesh = pv.read(opencmiss_solution_path)
    mesh = mesh.threshold(value=1, scalars="Structure", invert=False)

    # color = "bone"
    color = "bone_r"
    # color = "Pastel1"

    pl = pv.Plotter()
    pl.add_text(os.path.basename(opencmiss_solution_path))
    half_mesh = mesh.clip('y',
                           crinkle=False,)
    thresholded = half_mesh.threshold(
        value=1,
        scalars="Structure",
        invert=False,
    )
    pl.add_mesh(
        thresholded,
        scalars=solution_metric,
        cmap=color,
    )
    pl.view_xz()
    pl.add_axes(interactive=True)
    pl.camera.up = (0, 0, -1)

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
