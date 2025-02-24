"""
Visualize OpenCMISS results by calling `visualize_OpenCMISS_results()`
@params
:param `input_path`: /Path/to/input/mesh.mesh
:(optional) param `input_metric`: color map scalar for the result mesh, metric choices below:
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
import meshio
import argparse
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
        default=None,
    )
    parser.add_argument(
        "-c",
        "--clip",
        help="Clip the mesh in either 'x', 'y', or 'z'",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--thresh",
        help="Threshold visual cells based on a metric",
        default=None,
    )
    parser.add_argument(
        "-tv",
        "--thresh_val",
        help="Threshold value",
        default=1.0,
    )

    return parser.parse_args()


def str_lowercase(s: str) -> str:
    return s.lower()


def visualize_OpenCMISS_results(
    input_path: str,
    input_metric: str | None = None,
    clip: str | None = None,
    thresh: str | None = None,
    thresh_val: float = 1.0,
) -> None:
    """
    Visualize OpenCMISS results
    @params
    :param `input_path`: /Path/to/input/mesh.mesh
    :(optional) param `input_metric`: color map scalar for the result mesh, metric choices below:
    :(optional) param `clip`: 'x', 'y', 'z'
    :(optional) param `thresh`: 
    :(optional) param `thresh_val`: 
    @returns: Void
    @outputs: Visual plot of modelled object with chosen metric colormap
    """

    print("-- Visualizing OpenCMISS mesh adaptation, loading file:")
    print(f" - {os.path.basename(input_path)}")

    mesh = pv.read(input_path)

    # color = "bone"
    color = "bone_r"
    # color = "Pastel1"

    pl = pv.Plotter()
    pl.add_text(os.path.basename(input_path))
    if clip:
        mesh = mesh.clip(clip, crinkle=False)
    if thresh:
        mesh = mesh.threshold(
            value=thresh_val,
            scalars=thresh,
            invert=True,
        )
    pl.add_mesh(
        mesh,
        scalars=input_metric,
        cmap=color,
        show_edges=True,
    )
    pl.view_xz()
    pl.add_axes(interactive=True)
    # pl.scalar_bar.SetTitle("Implicit domain")
    pl.camera.up = (0, 0, -1)

    pl.show()


### Main -----------------------------------------------------------------------
if __name__ == "__main__":
    args = parse_arguments()

    visualize_OpenCMISS_results(
        args.input,
        args.imetric,
        args.clip,
        args.thresh,
        float(args.thresh_val),
    )
