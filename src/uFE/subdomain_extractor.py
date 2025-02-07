""" 
Generates .mesh and .sol file for MMG based zero level-set mesh adaptation
"""

# Imports ---------------------------------------------------------------------
import os, sys
import argparse
from pathlib import Path
import pyvista as pv
import subprocess

sys.path.insert(0, str(Path(__file__).parents[1]))
from utils.formatting import print_section, timer


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
        help="Input path to surface mesh .ply file",
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
        "-sd",
        "--subdomain",
        type=int,
        help="Subdomain to be extracted from the mesh - default is 3",
        default=3,
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
def handle_args_none_ouput_file(
    input_file: Path,
    output_file: Path | None = None,
) -> Path:
    if output_file is None:
        output_file = input_file.with_name(input_file.stem + "_extracted.mesh")

    return output_file


def run_mmg_extract(
    input_file: Path,
    output_file: Path,
    subdomain,
    debug,
) -> None:
    call_str = [
        "mmg3d",
        "-in",
        str(input_file),
        "-sol",
        "0",
        "-out",
        str(output_file),
        "-noinsert",
        "-noswap",
        "-nomove",
        "-nsd",
        str(subdomain),
    ]
    if debug:
        call_str += ["-d"]

    print(call_str)

    subprocess.call(call_str)


# Main ------------------------------------------------------------------------
@timer
def extract_subdomain(
    input_file: Path,
    output_file: Path | None = None,
    subdomain: int = 3,
    debug=False,
    visuals=False,
) -> (Path, float):

    print_section()
    print("-- Mesh extractor initiated, loading file:")
    print(f" - {input_file.name}")

    output_file = handle_args_none_ouput_file(input_file, output_file)

    run_mmg_extract(input_file, output_file, subdomain, debug)

    if visuals:
        extracted_mesh = pv.read(output_file)

        pl = pv.Plotter()
        pl.add_mesh(
            extracted_mesh,
            color="white",

        )
        pl.add_axes(interactive=True)
        pl.show()

    print("-- Meshing extraction complete, total time elapsed:")

    return output_file


if __name__ == "__main__":
    args = parse_arguments()

    output_file = Path(args.output) if args.output else args.output

    extract_subdomain(
        Path(args.input),
        output_file,
        args.subdomain,
        args.debug,
        args.visuals,
    )
