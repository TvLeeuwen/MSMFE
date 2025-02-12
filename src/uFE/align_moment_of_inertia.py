"""
Align surface mesh principal axes of inertia with the local coordinate system by calling `align_surface_mesh()`.

:param `input_file`: Path/to/input_file(.ply).
:param `output_file`: Path/to/output_file(.ply). :output aligned surface mesh .ply file of name `output_file`
"""


# Imports ---------------------------------------------------------------------
try:
    import os
    import sys
    import argparse
    from pathlib import Path
    import numpy as np
    import trimesh

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from utils.formatting import print_section, timer
    from utils.handle_args import handle_args_suffix

except ModuleNotFoundError as e:
    sys.exit(f"-- {e}")


# Parse args ------------------------------------------------------------------
def parse_arguments():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate an initial mesh for mmg based mesh adaptation",
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
        help="Input surface mesh (.ply)",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output filename (.ply)",
    )
    return parser.parse_args()


@timer
def write_output(input_file: Path, output_file: Path, mesh):
    print_section()

    if output_file is None:
        output_file = input_file.parents[0] / input_file.with_name(
            "aligned_" + input_file.name
        )

    # handle_args_dir_match(input_file, output_file)
    output_file = handle_args_suffix(output_file, ".ply")

    mesh.export(str(output_file))

    print(f"-- Writing:\n - {output_file.name}.")


def scale_factor(points, target_min=10, target_max=200):
    """
    Computes a uniform rescale factor for a point cloud to fit within a target range.
    
    :param points: NumPy array of shape (N, 3) representing XYZ coordinates.
    :param target_min: Minimum value of the rescaled range (default: 1).
    :param target_max: Maximum value of the rescaled range (default: 1000).
    :return: The scale factor and the shifted point cloud.
    """
    min_val = np.min(points)
    max_val = np.max(points)

    if min_val == max_val:
        raise ValueError("All points have the same value; mesn not valid.")

    # Compute a uniform scale factor
    scale_factor = (target_max - target_min) / (max_val - min_val)
    print(f" - Scaling mesh - factor: {scale_factor}")

    return scale_factor

# Main -----------------------------------------------------------------------
@timer
def align_surface_mesh(
    input_file: str,
    output_file: str = None,
):
    """
    Align surface mesh principal axes of inertia with the local coordinate system.

    :param `input_file`: Path/to/`input_file`(.ply).
    :param `output_file`: Path/to/`output_file`(.ply).
    :output aligned surface mesh .ply file of name `output_file`
    """

    print_section()
    print(f"-- Mesh alignment initiated - loading file: \n - {Path(input_file).name}")


    mesh = trimesh.load(input_file)

    print("-- Loading complete, aligning mesh...")
    inertia_tensor = mesh.moment_inertia
    eigenvalues, eigenvectors = np.linalg.eig(inertia_tensor)
    center_of_mass = mesh.center_mass
    rotation_matrix = eigenvectors.T

    transformation_matrix = np.eye(4)
    transformation_matrix[:3, :3] = rotation_matrix

    translation_to_origin = np.eye(4)
    translation_to_origin[:3, 3] = -center_of_mass

    translation_back = np.eye(4)
    translation_back[:3, 3] = center_of_mass

    full_transformation = (
        translation_back @ transformation_matrix @ translation_to_origin
    )

    mesh.apply_transform(full_transformation)

    mesh.vertices = mesh.vertices*scale_factor(mesh.vertices)

    write_output(input_file, output_file, mesh)

    print("-- Aligment complete, time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    output_file = Path(args.output) if args.output else args.output

    align_surface_mesh(
        args.input,
        output_file,
    )
