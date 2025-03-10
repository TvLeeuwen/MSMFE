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
    import os
    import sys
    import argparse
    import pymeshlab
    import pyvista as pv
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from utils.formatting import print_status, print_section, timer
    from utils.handle_args import handle_args_suffix
    from utils.default_parameters import DEFAULT_MAX_HOLE_SIZE
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

    print(f"-- Writing file:\n - {output_file}")
    meshset.save_current_mesh(str(output_file))

    if visual:
        import pyvista as pv

        mesh = pv.read(output_file)
        mesh.plot_normals(mag=0.003, flip=True, show_edges=True, color="red")

    return output_file


# Main -----------------------------------------------------------------------
@timer
def assure_surface_mesh_quality(
    input_file,
    output_file=None,
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
    print(f"-- Quality assurance initiated - loading file:\n - {os.path.basename(input_file)}")

    if os.path.splitext(input_file)[1] == ".vtp":
        print("   - .vtp detected - mesh alignment requires .ply")
        ply_file = os.path.splitext(output_file)[0] + ".ply"
        pv.read(input_file).save(ply_file)
        input_file = ply_file
        print(f"   - {input_file} written.")


    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(input_file))

    ms = check_and_fix_non_manifold(ms)
    ms = check_and_fix_holes(ms, max_hole_size)

    write_output(input_file, output_file, ms, visual=visuals)

    if visuals:
        mesh = pv.read(output_file)
        mesh.plot_normals(mag=0.003, flip=True, show_edges=True, color="red")


    print("-- Quality assurance finished, time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    assure_surface_mesh_quality(
        args.input,
        args.output,
        args.maxholesize,
        args.visuals,
    )
