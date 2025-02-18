"""
Generates .mesh and .sol file for MMG based zero level-set mesh adaptation
"""
import os
import sys
import argparse
import numpy as np
import pyvista as pv
import subprocess
from pathlib import Path

# sys.path.insert(0, str(Path(__file__).parents[2]))
from utils.formatting import print_status, return_timer, print_section
from utils.default_parameters import (
    DEFAULT_HAUSD,
    DEFAULT_HGRAD,
    DEFAULT_HMIN,
    DEFAULT_HMAX,
    DEFAULT_SUBDOMAIN,
    DEFAULT_MEMORY_MAX,
    DEFAULT_MESH_ITERATIONS,
)
from subdomain_extractor import extract_subdomain


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
        help="Path to initial mesh .mesh",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--surf",
        type=str,
        help="Path to surface mesh .ply file",
    )
    parser.add_argument(
        "-m",
        "--metric",
        type=str,
        help="Metric used for implicit boundary meshing, default='implicit_distance'",
        default="implicit_distance",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output filename ()",
        default=None,
    )
    parser.add_argument(
        "-hausd",
        "--hausd",
        type=float,
        help=f"Maximum Hausdorff distance for the boundaries approximation,\
        higher values refine higher curvatures - default: {DEFAULT_HAUSD}",
        default=DEFAULT_HAUSD,
    )
    parser.add_argument(
        "-hgrad",
        "--hgrad",
        type=float,
        help=f"Gradation value - default: {DEFAULT_HGRAD}",
        default=DEFAULT_HGRAD,
    )
    parser.add_argument(
        "-hmin",
        "--hmin",
        type=float,
        help=f"Minimum element edge size - default: {DEFAULT_HMIN}",
        default=DEFAULT_HMIN,
    )
    parser.add_argument(
        "-hmax",
        "--hmax",
        type=float,
        help=f"Maximum element edge size - default: {DEFAULT_HMAX}",
        default=DEFAULT_HMAX,
    )
    parser.add_argument(
        "-sd",
        "--subdomain",
        type=int,
        help=f"Subdomain to be extracted from the mesh - default: {DEFAULT_SUBDOMAIN}",
        default=DEFAULT_SUBDOMAIN,
    )
    parser.add_argument(
        "-mm",
        "--mem",
        type=int,
        help=f"Maximum memory size for mesh adaptation in MBs - default: {DEFAULT_MEMORY_MAX}",
        default=DEFAULT_MEMORY_MAX,
    )
    parser.add_argument(
        "-iter",
        "--iterations",
        type=int,
        help=f"Number of mesh adaptation iterations - default: {DEFAULT_MESH_ITERATIONS}",
        default=DEFAULT_MESH_ITERATIONS,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Activate debug mode for mmg feedback",
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
def handle_args_none_output_file(
    input_file: Path,
    output_file: Path | None = None,
):
    if output_file is None:
        output_file = input_file.with_name(
            input_file.name.replace("initial", "adapted")
        )

    return output_file


def handle_iterative(input_file: Path, output_file: Path, iter: int):
    if iter == 0:
        pass
    elif iter == 1:
        output_file = output_file.with_name(
            output_file.stem + f"_iteration_{iter}" + ".mesh"
        )
    else:
        input_file = output_file
        output_file = output_file.with_name(
            output_file.name.replace(f"_iteration_{iter-1}", f"_iteration_{iter}")
        )

    return input_file, output_file


def generate_sol_file(input_file, signed_distances):
    sol_file = input_file.with_name(input_file.name.replace(".mesh", ".sol"))

    with open(sol_file, "w") as file:
        file.write("MeshVersionFormatted 2" + "\n")
        file.write("Dimension 3" + "\n")
        file.write("SolAtVertices" + "\n")
        file.write(f"{len(signed_distances)}" + "\n")
        file.write("1 1" + "\n")
        for distance in signed_distances:
            file.write(f"{distance} \n")
        file.write("End" + "\n")

    print(f"-- Generating .sol file:\n - {sol_file.name}.")

    return sol_file


def run_mmg(
    input_file,
    sol_file,
    output_file,
    memory_max,
    hausd,
    hgrad,
    hmin,
    hmax,
    refine_iterations,
    iter,
    debug=False,
):
    print_section()
    if refine_iterations:
        print("-- Iterative mesh adaptation initiated")
        print(f" - Iteration {iter+1} out of {refine_iterations+1}")
    else:
        print("-- Mesh adaptation initiated")

    call_str = [
        "mmg3d",
        "-in",
        str(input_file),
        "-sol",
        str(sol_file),
        "-out",
        str(output_file),
        "-ls",
        "0",
        "-m",
        str(memory_max),
        "-nr",
        "-hausd",
        str(hausd),
        "-hgrad",
        str(hgrad),
        "-hmin",
        str(hmin),
        "-hmax",
        str(hmax),
    ]

    if debug:
        call_str += ["-d"]

    subprocess.call(call_str)


# Main ------------------------------------------------------------------------
@return_timer
def generate_implicit_domain_volumetric_mesh(
    input_file: Path,
    surf_file: Path,
    output_file: Path | None = None,
    metric: str = "implicit_distance",
    hausd: float = DEFAULT_HAUSD,
    hgrad: float = DEFAULT_HGRAD,
    hmin: float = DEFAULT_HMIN,
    hmax: float = DEFAULT_HMAX,
    extract_domain: int = DEFAULT_SUBDOMAIN,
    memory_max: int = DEFAULT_MEMORY_MAX,
    refine_iterations: int = DEFAULT_MESH_ITERATIONS,
    debug: bool = False,
    visuals: bool = False,
) -> None:
    print_section()
    print("-- Initiating mesh adaptation, loading files:")
    print(f" - {input_file.name}\n - {surf_file.name}")

    for iter in range(0, refine_iterations + 1):
        output_file = handle_args_none_output_file(input_file, output_file)
        input_file, output_file = handle_iterative(input_file, output_file, iter)

        mesh = pv.read(input_file)
        surf = pv.read(surf_file)

        print_status(
            "-- Volumetric mesh loaded, mesh bounds: ",
            f"{[bound for bound in mesh.bounds]}",
        )

        if visuals:
            cells = mesh.cells.reshape(-1, 5)[:, 1:]
            cell_center = mesh.points[cells].mean(1)
            cutting_plane = 2
            half = np.mean(
                [surf.bounds[cutting_plane * 2], surf.bounds[(cutting_plane * 2) + 1]]
            )
            mask = cell_center[:, cutting_plane] < half
            cell_ind = mask.nonzero()[0]

        if metric == "implicit_distance":
            print("-- Computing signed distances")
            mesh.compute_implicit_distance(surf, inplace=True)


        if visuals:
            subgrid = mesh.extract_cells(cell_ind)

            plotter = pv.Plotter()
            plotter.add_mesh(
                subgrid,
                show_edges=True,
                scalars=metric,
                cmap="coolwarm",
                clim=[-1, 1],
            )
            if metric == "implicit_distance":
                plotter.add_mesh(surf, lighting=True, color="white", scalars=None)

            plotter.show()

        signed_distances = mesh[metric]

        sol_file = generate_sol_file(input_file, signed_distances)

        run_mmg(
            input_file,
            sol_file,
            output_file,
            memory_max,
            hausd,
            hgrad,
            hmin,
            hmax,
            refine_iterations,
            iter,
            debug=debug,
        )

    if extract_domain:
        extract_subdomain(
            output_file,
            subdomain=extract_domain,
            debug=debug,
            visuals=visuals,
        )

    print("-- Volumetric meshing complete, total time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    output_file = Path(args.output) if args.output else args.output

    generate_implicit_domain_volumetric_mesh(
        Path(args.input),
        Path(args.surf),
        output_file,
        args.metric,
        args.hausd,
        args.hgrad,
        args.hmin,
        args.hmax,
        args.subdomain,
        args.mem,
        args.iterations,
        args.debug,
        args.visuals,
    )
