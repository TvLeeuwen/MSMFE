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
def call_surface_remesher(
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
            "src/uFE/surface_remesher.py",
            "-i",
            f"{mesh_file}",
            "-o",
            f"{output_file}",
            "-v",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


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
            # "-v",
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
            # "-v",
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
    metric="implicit_distance",
    hausd=DEFAULT_HAUSD,
    hgrad=DEFAULT_HGRAD,
    hmin=DEFAULT_HMIN,
    hmax=DEFAULT_HMAX,
    extract_subdomain=DEFAULT_SUBDOMAIN,
    mem_max=DEFAULT_MEMORY_MAX,
    refine_iterations=DEFAULT_MESH_ITERATIONS,
    debug=None,
):
    print("-- Running implicit domain volumetric mesh generator...")
    command = [
        "conda",
        "run",
        "-n",
        "envMSM_FE",
        "python",
        "src/uFE/implicit_domain_volumetric_mesh_generator.py",
        "-i",
        mesh_file,
        "-o",
        output_file,
        "-m",
        metric,
        "-hausd",
        f"{hausd}",
        "-hgrad",
        f"{hgrad}",
        "-hmin",
        f"{hmin}",
        "-hmax",
        f"{hmax}",
        "-sd",
        f"{extract_subdomain}",
        "-mm",
        f"{mem_max}",
        "-iter",
        f"{refine_iterations}",
        # "-d",
        "-v",
    ]
    if surf_file:
        command.extend(
            [
                "-s",
                surf_file,
            ]
        )
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


def call_assign_boundary_conditions_manually(
    mesh_path,
    output_base,
    surf_select=True,
    txt=False,
):
    command = [
        "conda",
        "run",
        "-n",
        "envMSM_FE",
        "python",
        "src/uFE/assign_boundary_conditions_manually.py",
        "-i",
        f"{mesh_path}",
        "-o",
        f"{output_base}",
    ]
    if surf_select:
        command.extend(
            [
                "-s",
            ]
        )
    if txt:
        command.extend(
            [
                "-t",
            ]
        )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if "neumann" in result.stdout:
        return result, True, True
    elif "dirichlet" in result.stdout and "neumann" not in result.stdout:
        return result, True, False
    else:
        return result, False, False


def call_bc_visualizer(
    mesh_path,
    dirichlet_path,
    neumann_path,
):
    command = [
        "conda",
        "run",
        "-n",
        "envMSM_FE",
        "python",
        "src/uFE/bc_visualizer.py",
        "-i",
        mesh_path,
    ]
    if dirichlet_path:
        command.extend(
            [
                "-d",
                dirichlet_path,
            ]
        )
    if neumann_path:
        command.extend(
            [
                "-n",
                neumann_path,
            ]
        )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


def call_design_domain_generator(
    mesh_path,
    design_path
):
    command = [
        "conda",
        "run",
        "-n",
        "envMSM_FE",
        "python",
        "src/uFE/design_domain_generator.py",
        "-i",
        mesh_path,
        "-o",
        design_path,
        # "-t"
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


def call_open_cmiss(
    mesh_path,
    dirichlet_path,
    neumann_path,
    design_path,
):
    command = [
        "conda",
        "run",
        "-n",
        "envMSM_FE",
        "python",
        "src/uFE/opencmiss_linear_elasticity.py",
        "-i",
        mesh_path,
        "-d",
        dirichlet_path,
        "-n",
        neumann_path,
    ]
    if design_path:
        command += ["-dd", design_path]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


def call_combine_opencmiss_multiblock(
    opencmiss_solution_path,
    combined_opencmiss_solution_path,
):
    result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "envMSM_FE",
            "python",
            "src/uFE/combine_opencmiss_multiblock.py",
            "-i",
            opencmiss_solution_path,
            "-o",
            combined_opencmiss_solution_path,
            # "-v"
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result


def call_visualize_opencmiss(
    mesh_path,
    metric,
    clip=None,
    thresh=None,
    thresh_val=1.0,
):
    command = [
        "conda",
        "run",
        "-n",
        "envMSM_FE",
        "python",
        "src/uFE/visualize_opencmiss.py",
        "-i",
        mesh_path,
    ]
    if metric:
        command += ["-im", metric]
    if clip:
        command += ["-c", clip]
    if thresh:
        command += ["-t", thresh, "-tv", str(thresh_val),]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result
