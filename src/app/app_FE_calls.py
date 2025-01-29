# Imports ---------------------------------------------------------------------
import subprocess


# Defs ------------------------------------------------------------------------
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
    # print(result.args)
    print(result.stdout)
    print(result.stderr)
    # return result


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
    print(result.stderr)
    # return result


def call_implicit_domain_volumetric_mesh_generator(

):
    pass
