# Imports ---------------------------------------------------------------------
import subprocess
from src.uFE.utils.default_parameters import (
    DEFAULT_HAUSD,
    DEFAULT_HGRAD,
    DEFAULT_HMIN,
    DEFAULT_HMAX,
    DEFAULT_SUBDOMAIN,
    DEFAULT_MEMORY_MAX,
    DEFAULT_MESH_ITERATIONS,
)


# Defs ------------------------------------------------------------------------
def call_qa_highres_surface(
    mesh_file,
    output_file,
):
    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "envMSM_FE",
            "python",
            "src/uFE/qa_highres_surface.py",
            "-i",
            f"{mesh_file}",
            "-o",
            f"{output_file}",
        ],
        capture_output=True,
        text=True,
    )
    # print(result.args)
    print(result.stdout)
    return result


def call_align_moment_of_inertia(
        mesh_file,
        output_file,
):
    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "envMSM_FE",
            "python",
            "src/uFE/align_moment_of_inertia.py",
            "-i",
            f"{mesh_file}",
            "-o",
            f"{output_file}",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


def call_initial_volumetric_mesher(
    mesh_file,
    output_file,
    element_size,
):
    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "envMSM_FE",
            "python",
            "src/uFE/initial_volumetric_mesh_generator.py",
            "-i",
            f"{mesh_file}",
            "-o",
            f"{output_file}",
            "-s",
            f"{element_size}",
            "-v",
        ],
        capture_output=True,
        text=True,
    )
    # print(result.args)
    print(result.stdout)
    return result


def call_implicit_domain_volumetric_mesh_generator(
    mesh_file,
    surf_file,
    output_file,
    hausd=DEFAULT_HAUSD,
    hgrad=DEFAULT_HGRAD,
    hmin=DEFAULT_HMIN,
    hmax=DEFAULT_HMAX,
    subdomain=DEFAULT_SUBDOMAIN,
    mem_max=DEFAULT_MEMORY_MAX,
    refine_iterations=DEFAULT_MESH_ITERATIONS,
    debug=None,
):
    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "envMSM_FE",
            "python",
            "src/uFE/implicit_domain_volumetric_mesh_generator.py",
            "-i",
            f"{mesh_file}",
            "-s",
            f"{surf_file}",
            "-o",
            f"{output_file}",
            "-hausd",
            f"{hausd}",
            "-hgrad",
            f"{hgrad}",
            "-hmin",
            f"{hmin}",
            "-hmax",
            f"{hmax}",
            "-sd",
            f"{subdomain}",
            "-m",
            f"{mem_max}",
            "-iter",
            f"{refine_iterations}",
            # "-d",
            "-v",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result
