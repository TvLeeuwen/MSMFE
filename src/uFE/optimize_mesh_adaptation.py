"""
Optimize mesh adaptation based on signed distance RMSE
"""


# Imports ---------------------------------------------------------------------
import os, sys
from pathlib import Path
import datetime
from scipy.optimize import minimize

from utils.structure import check_project_directory
from utils.formatting import timer, print_status, print_section

from defaults.default_parameters import (
    DEFAULT_HAUSD,
    DEFAULT_HGRAD,
    DEFAULT_HMIN,
    DEFAULT_HMAX,
)

from uFE.implicit_domain_volumetric_mesh_generator import (
    generate_implicit_domain_volumetric_mesh,
)
from uFE.subdomain_extractor import extract_subdomain
from uFE.mesh_comparison import compare_meshes


# Defs ------------------------------------------------------------------------
def objective_function(
    params,
    input_file: Path,
    surf_file: Path,
    rmse_file: Path,
    save_meshes: bool = False,
    visuals: bool = False,
):
    """
    Generates implicit domain volumetric mesh, extracts the resulting geometry,
    and compares the result with the orginal geometry. Returns RMSE.
    """
    print_section(repeat=2)
    hausd, hgrad, hmin, hmax = params
    print_status("-- Testing parameters: hausd, hgrad, hmin, hmax: ", f"{hausd:.2f}, {hgrad:.2f}, {hmin:.2f}, {hmax:.2f}")

    output_file = (input_file.parent / ".optim" / input_file.name).with_name(
        input_file.stem + f"_optim_{hausd}_{hgrad}_{hmin}_{hmax}.mesh"
    )
    check_project_directory(input_file.parent / ".optim", verbose=False)

    _, adaptive_meshing_time = generate_implicit_domain_volumetric_mesh(
        input_file,
        surf_file,
        output_file,
        hausd,
        hgrad,
        hmin,
        hmax,
        refine_iterations=0,
    )

    extracted_adapted_mesh_file, time_extract = extract_subdomain(
        output_file,
        debug=False,
        visuals=visuals,
    )

    rmse = compare_meshes(extracted_adapted_mesh_file, surf_file, visuals=visuals)

    with open(rmse_file, "a") as file:
        file.write(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - hausd: {hausd:.4f}, hgrad: {hgrad:.4f}, hmin: {hmin:.4f}, hmax: {hmax:.4f}, meshing time: {adaptive_meshing_time:.2f} s, RMSE: {rmse:.4f}\n"
        )

    if not save_meshes:
        os.remove(output_file)
        os.remove(output_file.with_suffix(".sol"))
        os.remove(extracted_adapted_mesh_file)
        os.remove(extracted_adapted_mesh_file.with_suffix(".sol"))
        os.remove(extracted_adapted_mesh_file.with_suffix(".vtu"))

    return rmse


# Main ------------------------------------------------------------------------
def optimize_mesh(
    input_file: Path,
    surf_file: Path,
    rmse_file: Path | None = None,
    initial=None,
    bounds=None,
    output_file: Path | None = None,
    save_meshes: bool = False,
    visuals: bool = False,
):
    # Code that recursively:
    # - sets input parameters (start with defaults or something bounding box / element size related)
    # - runs mesh adaptation module
    # - extracts surface mesh
    # - compares geometry by means of signed distance rmse (track with .out)
    # - check for improvement OR meet threshold
    # -- check effect of various imput parameters
    # -- take into account iterations

    print("-- Mesh optimization initiated")
    initial_guess = [.3, DEFAULT_HGRAD, DEFAULT_HMIN, DEFAULT_HMAX] if initial is None else initial
    bounds = [(.01, .5), (1.0, 1.5), (0.1, 10), (10, 200)]

    rmse_file = (
        (input_file.parent / ".optim" / input_file.name).with_name("mesh_optim.out") if rmse_file is None else rmse_file
    )

    with open(rmse_file, "a") as file:
        file.write(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Optimising parameters: HAUSD, HGRAD, HMIN, HMAX - initial guess: {initial_guess}, bounds: {bounds}\n"
        )

    # Powell because non-smooth / noisy RMSE landscape, does support bounds
    result = minimize(
        objective_function,
        initial_guess,
        args=(input_file, surf_file, rmse_file, save_meshes, visuals,),
        method="Powell",
        bounds=bounds,
        options={"maxiter": 10},
    )

    print(result.success)
    print(result.x)
    print(result.nit)

    with open(rmse_file, "a") as file:
        file.write(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Optimisation complete, success: {result.succes}, number of iteration: {result.nit}, final parameters: {result.x}, final RMSE: {result.fun}\n"
        )


if __name__ == "__main__":
    args = parse_arguments()

    output_file = Path(args.output) if args.output else args.output

    optimize_mesh(
        Path(args.input),
        Path(args.surf),
        output_file,
        args.visuals,
    )
