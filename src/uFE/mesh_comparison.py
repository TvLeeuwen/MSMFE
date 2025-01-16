"""
Compare an adapted (.mesh) mesh to a surface (.ply) mesh and output a signed distance based rmse to indicate similarity.
"""

# Imports ---------------------------------------------------------------------
import os, sys
import argparse
from pathlib import Path
import meshio
import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).parents[1]))
from utils.formatting import print_section, print_status


# Parse args ------------------------------------------------------------------
def parse_arguments():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Compare an adapted (.mesh) mesh to a surface (.ply) mesh and output a signed distance based rmse to indicate similarity.",
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
        help="Path to adapted mesh (.mesh) file",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--surface",
        type=str,
        help="Path to surface (.ply) file containing the geometry to be compared to",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------


# Main ------------------------------------------------------------------------
def compare_meshes(
    adapted_mesh_file: Path,
    original_surf_file: Path,
    visuals: bool = False,
):
    print_section()
    print("-- Mesh comparison initiated, loading files:")
    print(f" - {original_surf_file.name}\n - {adapted_mesh_file.name}")

    original_mesh = pv.read(original_surf_file)

    adapted_mesh = meshio.read(adapted_mesh_file)
    adapted_vtu_path = adapted_mesh_file.with_name(
        adapted_mesh_file.name.replace(".mesh", ".vtu")
    )
    meshio.write(adapted_vtu_path, adapted_mesh)
    adapted_mesh = pv.read(adapted_vtu_path)

    adapted_mesh.compute_implicit_distance(original_mesh, inplace=True)

    signed_distances = adapted_mesh.point_data["implicit_distance"]

    rmse = np.sqrt(np.mean(np.square(signed_distances)))

    print_status("-- Mesh comparison complete, RMSE:", f"{rmse:.4f}")

    if visuals:
        max_distance = np.max(np.abs(signed_distances))
        max_divergence_sign = "" if np.max(signed_distances) == max_distance else "-"

        plotter = pv.Plotter()
        plotter.add_mesh(
            adapted_mesh,
            scalars="implicit_distance",
            cmap="bwr",
            clim=[c * 0.1 for c in [-max_distance, max_distance]],
        )
        plotter.add_mesh(original_mesh, color="white")
        plotter.add_text(
            f"\nMaximum divergence: {max_divergence_sign}{max_distance:.2f}\n RMSE: {rmse:.4f}",
            position="upper_edge",
        )
        plotter.show()

    return rmse


if __name__ == "__main__":
    args = parse_arguments()

    compare_meshes(
        Path(args.input),
        Path(args.surface),
        args.visuals,
    )
