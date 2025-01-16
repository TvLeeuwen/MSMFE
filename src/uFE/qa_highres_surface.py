"""
Assure surface mesh quality using MeshLab api methods by calling `assure_surface_mesh_quality()`

:param `input_file`: Path/to/qa/unaproved/surface/mesh(.ply)
:(optional) param `output_file`: Path/to/ouput/surface/mesh(.ply)
:(optional) param `max_hole_size`: Set maximum hole size to be filled during mesh repair.
:(optional) param `visuals`: Toggle visual feedback
:output quality assured surface mesh .ply file of name `output_file`
"""

# import
try:
    import sys
    import argparse
    from pathlib import Path
    import pymeshlab

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from utils.formatting import print_status, print_section, timer
    from utils.handle_args import handle_args_dir_match, handle_args_suffix
except ModuleNotFoundError as e:
    sys.exit(f"-- {e}")

# Default params --------------------------------------------------------------
DEFAULT_MAX_HOLE_SIZE = 500


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
    parser.add_argument(
        "-m",
        "--maxholesize",
        type=int,
        default=DEFAULT_MAX_HOLE_SIZE,
        help="Maximum hole size",
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Acticate visual feedback",
    )
    return parser.parse_args()


def check_and_fix_non_manifold(ms):
    topological_measures = ms.get_topological_measures()

    print_status(
        " - Number of non-manifold vertices detected",
        f"{topological_measures['non_two_manifold_vertices']}",
    )
    print_status(
        " - Number of non-manifold edges detected",
        f"{topological_measures['non_two_manifold_edges']}",
    )

    if topological_measures["non_two_manifold_vertices"] != 0:
        print("-- Repairing non-manifold vertices...")
        ms.meshing_repair_non_manifold_vertices()

        topological_measures = ms.get_topological_measures()

        print_status(
            " - Done, non-manifold vertices remaining:",
            f"{topological_measures['non_two_manifold_vertices']}",
        )

    if topological_measures["non_two_manifold_edges"] != 0:
        print("-- Repairing non-manifold edges...")
        ms.meshing_repair_non_manifold_edges()

        topological_measures = ms.get_topological_measures()
        print_status(
            " - Done, non-manifold edges remaining:",
            f"{topological_measures['non_two_manifold_edges']}",
        )

    return ms


def check_and_fix_holes(ms, max_hole_size):
    topological_measures = ms.get_topological_measures()

    print_status(
        "-- Number of holes detected", f"{topological_measures['number_holes']}"
    )

    if topological_measures["number_holes"] != 0:
        print(f"-- Repairing holes below size of {max_hole_size} elements:")
        ms.meshing_close_holes(maxholesize=max_hole_size, refinehole=True)

        print_status(
            " - Done, holes remaining:",
            f"{ms.apply_filter('get_topological_measures')['number_holes']}",
        )

    return ms


@timer
def write_output(
    input_file: Path,
    output_file: Path | None,
    meshset,
    visual=False,
):
    print_section()

    if output_file is None:
        output_file = input_file.parents[0] / input_file.with_name(
            "QA_approved_" + input_file.name
        )

    handle_args_dir_match(input_file, output_file)
    output_file = handle_args_suffix(output_file, ".ply")

    print(f"-- Writing file:\n - {output_file}")
    meshset.save_current_mesh(str(output_file))

    if visual:
        import pyvista as pv

        plotter = pv.Plotter()
        plotter.add_mesh(pv.read(output_file), color="white", scalars=None)
        plotter.show()

    return output_file


# Main -----------------------------------------------------------------------
@timer
def assure_surface_mesh_quality(
    input_file: Path,
    output_file: Path | None = None,
    max_hole_size: int = DEFAULT_MAX_HOLE_SIZE,
    visuals: bool = False,
) -> None:
    """
    Assures surface mesh quality using MeshLab api methods.

    :param `input_file`: Path/to/qa/unaproved/surface/mesh(.ply)
    :(optional) param `output_file`: Path/to/ouput/surface/mesh(.ply)
    :(optional) param `max_hole_size`: Set maximum hole size to be filled during mesh repair.
    :(optional) param `visuals`: Toggle visual feedback
    :output quality assured surface mesh .ply file of name `output_file`
    """

    print_section()
    print(f"-- Quality assurance initiated - loading file:\n - {input_file.name}")

    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(input_file))

    ms = check_and_fix_non_manifold(ms)

    ms = check_and_fix_holes(ms, max_hole_size)

    write_output(input_file, output_file, ms, visual=visuals)

    print("-- Quality assurance finished, time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    output_file = Path(args.output) if args.output else args.output

    assure_surface_mesh_quality(
        Path(args.input),
        output_file,
        args.maxholesize,
        args.visuals,
    )
