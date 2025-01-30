"""
Generate initial .mesh for mmg based mesh adaptation using tetgen by calling `generate_initial_volumetric_mesh()`

:param `input_file`: /Path/to/input/mesh.ply
:(optional) param `output_file`: /Path/to/output/mesh(.mesh)
:(optional) param `element_size`: Integer preferred element size
:(optional) param `visuals`: Toggle visual feedback
:output volumetric mesh  of name `output_file` with:
:: Mesh dimensions of `input_file`'s bounding box file
:: Elements sized approxiately `element_size`
"""

# Imports ---------------------------------------------------------------------
import argparse
from pathlib import Path
import sys
import numpy as np
import pyvista as pv
import tetgen
import meshio

sys.path.insert(0, str(Path(__file__).parents[2]))
print(str(Path(__file__).parents[2]))
from src.uFE.utils.formatting import print_section, timer
from src.uFE.utils.handle_args import (
    handle_args_suffix,
    handle_args_integer,
)


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
        "-s",
        "--size",
        type=int,
        help=f"Approximate mesh element size, default=100",
        default=100,
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
def generate_bounding_box(
    surf,
    buffer: int = 3,
    visual: bool = False,
):
    """
    Generate bounding box around surface geometry with added buffer.

    :param surf [TODO:type]: [TODO:description]
    :param buffer [TODO:type]: [TODO:description]
    :param visual [TODO:type]: [TODO:description]
    """

    box_bounds = [
        # b - buffer if i % 2 == 0 else b + buffer
        int(b - buffer) if i % 2 == 0 else int(b + buffer)
        for i, b in enumerate(surf.bounds)
    ]

    surf_box = pv.Box(bounds=box_bounds, level=8, quads=False)

    if visual:
        pl = pv.Plotter()
        pl.add_axes(interactive=True)
        pl.add_mesh(surf, lighting=True, color="white", scalars=None)
        pl.show()

    return surf_box


def tetgen_surf_box(
    surf_box,
    surf,
    element_size,
    visual: bool = False,
):
    tet = tetgen.TetGen(surf_box)

    tet.tetrahedralize(switches=f"qa{element_size}Q")

    if visual:
        cells = tet.grid.cells.reshape(-1, 5)[:, 1:]
        cell_center = tet.grid.points[cells].mean(1)
        cutting_plane = 2
        half = np.mean(
            [surf.bounds[cutting_plane * 2], surf.bounds[(cutting_plane * 2) + 1]]
        )
        mask = cell_center[:, cutting_plane] < half
        cell_ind = mask.nonzero()[0]
        subgrid = tet.grid.extract_cells(cell_ind)

        pl = pv.Plotter()
        pl.add_mesh(surf, lighting=True, color="white", scalars=None)
        pl.add_mesh(subgrid, lighting=True, show_edges=True)
        pl.add_axes(interactive=True)
        pl.show()

    return tet


# @timer
def write_output(
    input_file: Path,
    output_file: Path | None,
    vol_box,
    element_size: int,
):
    print_section()

    if output_file is None:
        output_file = input_file.with_name(
            "initial_"
            + input_file.stem.replace("surface", f"size{element_size}_volumetric")
        ).with_suffix(".mesh")

    output_file = handle_args_suffix(output_file)
    # handle_args_dir_match(input_file, output_file)

    vtu_path = (output_file.parents[0] / output_file.stem).with_suffix(".vtu")

    print(f"-- Writing files:\n - {output_file.name}\n - {output_file.stem}.vtu.")

    vol_box.write(vtu_path, binary=False)
    # read in as with meshio for conversion to .mesh
    mesh = meshio.read(vtu_path)
    meshio.write(output_file, mesh)


# Main ------------------------------------------------------------------------
@timer
def generate_initial_volumetric_mesh(
    input_file: Path,
    output_file: Path | None = None,
    element_size: int = 1,
    visuals: bool = False,
) -> None:
    """
    Generates initial .mesh for mmg based mesh adaptation using tetgen.

    :param `input_file`: /Path/to/input/mesh.ply
    :(optional) param `output_file`: /Path/to/output/mesh(.mesh)
    :(optional) param `element_size`: Integer preferred element size
    :(optional) param `visuals`: Toggle visual feedback
    :output volumetric mesh  of name `output_file` with:
    :: Mesh dimensions of `input_file`'s bounding box file
    :: Elements sized approxiately `element_size`
    """

    handle_args_integer(element_size)

    print_section()
    print(f"-- Volumetric mesher initiated - loading file:\n - {input_file}")

    surf = pv.read(input_file)

    surf_box = generate_bounding_box(surf, visual=False)

    vol_box = tetgen_surf_box(
        surf_box,
        surf,
        element_size=element_size,
        visual=visuals,
    )

    write_output(
        input_file,
        output_file,
        vol_box,
        element_size,
    )

    print("-- Initial volumetric mesh generated - time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    output_file = Path(args.output) if args.output else args.output

    generate_initial_volumetric_mesh(
        Path(args.input),
        output_file,
        args.size,
        args.visuals,
    )
