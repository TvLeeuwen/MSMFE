# Imports ---------------------------------------------------------------------
import os
import shutil
from numpy import half
import pandas as pd
import pyvista as pv
import streamlit as st
from pathlib import Path

from src.MSM.sto_generator import generate_sto, read_input, write_columns
from src.MSM.moco_track_kinematics import moco_track_states
from src.MSM.force_vector_extractor import (
    extract_force_vectors,
    extract_model_bone_and_muscle,
)
from src.app.app_visuals import click_visual_toi_selector
from src.app.app_FE_calls import (
    call_surface_remesher,
    call_qa_highres_surface,
    call_initial_volumetric_mesher,
    call_align_moment_of_inertia,
    call_implicit_domain_volumetric_mesh_generator,
    call_assign_boundary_conditions_manually,
    call_design_domain_generator,
    call_bc_visualizer,
    call_open_cmiss,
    call_combine_opencmiss_multiblock,
    call_visualize_opencmiss,
)

sts = st.session_state


# Defs ------------------------------------------------------------------------
def generate_kinematics(osim_path, kine_path, output_path):
    kinematics_path = generate_sto(
        Path(kine_path),
        model_file=Path(osim_path),
    )
    sts.kinematics_path = os.path.join(output_path, str(kinematics_path))
    st.success("Kinematics successfully generated!")


def track_kinematics(moco_path, osim_path, output_path):
    st.write("Tracking kinematics...")
    run_moco(
        moco_path,
        osim_path,
        output_path,
    )
    st.success("Tracking succesful!")


def run_moco(moco_path, osim_path, output_path):
    try:
        os.chdir(output_path)
        filter_params = {
            "state_filters": ["jointset"],
            "invert_filter": False,
        }
        solution_path, muscle_dynamics_path = moco_track_states(
            Path(osim_path),
            Path(sts.kinematics_path),
            filter_params,
        )
        os.chdir(moco_path)

        sts.moco_solution_path = os.path.join(output_path, str(solution_path))

        sts.moco_solution_dynamics_path = os.path.join(
            output_path, str(muscle_dynamics_path)
        )
    except Exception as e:
        st.error(f"An error occurred: {e}")
        os.chdir(moco_path)


def calculate_total_muscle_force(
    dynamics_path,
):
    df, _ = read_input(dynamics_path)

    muscles = list(
        set(
            [key.split("|")[0].split("/")[-1] for key in df.keys() if "time" not in key]
        )
    )

    df2 = pd.DataFrame(0, index=range(len(df["time"])), columns=["time"])
    df2["time"] = df["time"]
    for muscle in muscles:
        df2[f"{muscle}|total_muscle_force"] = (
            df[f"/forceset/{muscle}|active_fiber_force"]
            + df[f"/forceset/{muscle}|passive_fiber_force"]
            + df[f"/forceset/{muscle}|tendon_force"]
        )

    muscle_forces_path = dynamics_path.replace("dynamics.sto", "forces.json")
    pd.DataFrame(df2).to_json(muscle_forces_path, orient="records", lines=True)

    return muscle_forces_path


def bone_muscle_extraction(model):
    bone_muscle_map = extract_model_bone_and_muscle(model)

    return bone_muscle_map


def force_vector_extraction(model, sto_data, boi, output_path):
    if st.button(f"Extract {boi} force vectors"):
        with st.spinner("Extracting vectors..."):
            try:
                (
                    sts.force_origins_path,
                    sts.force_vectors_path,
                ) = extract_force_vectors(model, sto_data, boi, output_path)

            except Exception as e:
                st.error(f"An error occurred: {e}")
            st.success(f"Extraction: {boi} succesful")


def toi_selector(sto, muscles):
    df, _ = read_input(sto)
    df2 = pd.DataFrame(0, index=range(len(df["time"])), columns=["time"])
    df2["time"] = df["time"]
    for col in df.columns:
        if "active_fiber_force" in col:
            for muscle in muscles:
                if muscle in col:
                    df2[col] = df[col]
    if "toi" not in sts:
        sts.toi = None
    click_visual_toi_selector(df2)


def remesh_surface(
    mesh_file,
    output_path,
):
    with st.spinner("Remeshing surface..."):
        remesh_file = os.path.join(
            output_path,
            os.path.splitext("uFE_remeshed_" + os.path.basename(mesh_file))[0] + ".ply",
        )
        result = call_surface_remesher(
            mesh_file,
            remesh_file,
        )
        if result.returncode:
            return result

        # qa_file = os.path.splitext(remesh_file)[0] + "_qa.ply"
        # result = call_qa_highres_surface(
        #     mesh_file,
        #     qa_file,
        # )
        # if result.returncode:
        #     return result

        return result


def generate_volumetric_mesh(
    mesh_file,
    output_path,
    element_size,
):
    """
    [TODO:description]

    :param mesh_file [TODO:type]: [TODO:description]
    :param element_size [TODO:type]: [TODO:description]
    """
    with st.spinner("Generating mesh..."):
        qa_file = os.path.join(
            output_path,
            os.path.splitext("uFE_" + os.path.basename(mesh_file))[0] + "_qa.ply",
        )
        result = call_qa_highres_surface(
            mesh_file,
            qa_file,
        )
        if result.returncode:
            return result
        st.warning("Surface mesh quality assessment complete..")

        aligned_file = os.path.splitext(qa_file)[0] + "_aligned.ply"
        result = call_align_moment_of_inertia(
            qa_file,
            aligned_file,
        )
        if result.returncode:
            return result
        st.warning("Surface mesh aligment complete..")

        initial_file = os.path.splitext(aligned_file)[0] + "_initial.mesh"
        result = call_initial_volumetric_mesher(
            aligned_file,
            initial_file,
            element_size,
        )
        if result.returncode:
            return result
        st.warning("Initial volumetric mesh complete..")

        volume_file = os.path.splitext(aligned_file)[0] + "_volumetric.mesh"
        extract_domain = 3
        result = call_implicit_domain_volumetric_mesh_generator(
            initial_file,
            aligned_file,
            volume_file,
            metric="implicit_distance",
            hausd=1e0,
            hgrad=1.3,
            hmin=1e-2,
            hmax=1e0,
            extract_subdomain=extract_domain,
            mem_max=16000,
            refine_iterations=0,
        )
        if result.returncode:
            return result, None

        if extract_domain:
            volume_file = os.path.splitext(volume_file)[0] + "_extracted.mesh"

        return result, volume_file


def manual_BC_selector(
    mesh_path,
    surf_select,
    txt,
):
    with st.spinner("Selecting boundary conditions"):
        if (
            "dirichlet_path" in sts
            and sts.dirichlet_path is not None
            and os.path.isfile(sts.dirichlet_path)
        ):
            os.unlink(sts.dirichlet_path)
        if (
            "neumann_path" in sts
            and sts.neumann_path is not None
            and os.path.isfile(sts.neumann_path)
        ):
            os.unlink(sts.neumann_path)

        result, dirichlet, neumann = call_assign_boundary_conditions_manually(
            mesh_path,
            os.path.splitext(mesh_path)[0],
            surf_select,
            txt,
        )
        if dirichlet:
            sts.dirichlet_path = (
                os.path.splitext(mesh_path)[0] + "_manual_dirichlet_BC.json"
            )
        if neumann:
            sts.neumann_path = os.path.splitext(mesh_path)[0] + "_manual_neumann_BC.json"

        if not os.path.isfile(sts.dirichlet_path):
            st.warning("Warning: No BCs were selected")

        if result.returncode:
            st.error("Failed to select boundary conditions")
            print(result.stderr)

        generate_design_domain(mesh_path)


def generate_design_domain(
    mesh_path,
):
    sts.design_path = os.path.splitext(mesh_path)[0] + "_design_domain.json"
    result = call_design_domain_generator(mesh_path, sts.design_path)
    if result.returncode:
        st.error("Failed to generated design domain")
        print(result.stderr)


def visualize_BCs(
    mesh_path,
    dirichlet_path,
    neumann_path=None,
):
    with st.spinner("Showing boundary conditions..."):
        dirichlet_file = dirichlet_path if os.path.isfile(dirichlet_path) else None
        if sts.neumann_path is not None:
            neumann_file = neumann_path if os.path.isfile(neumann_path) else None
        else:
            neumann_file = None

        if dirichlet_file is None:
            st.warning("Warning: No BCs were selected")

        result = call_bc_visualizer(
            mesh_path,
            dirichlet_file,
            neumann_file,
        )
        if result.returncode:
            st.error("Failed to visualize selected boundary conditions")
            print(result.stderr)


def run_open_cmiss(
    mesh_path,
    dirichlet_path,
    neumann_path,
    design_path,
):
    with st.spinner("Running Finite Element Analysis..."):
        result = call_open_cmiss(
            mesh_path,
            dirichlet_path,
            neumann_path,
            design_path,
        )
        if result.returncode:
            st.error("Failed run OpenCMISS")
            print(result.stderr)


def combine_opencmiss_solution(
    result_dir,
):
    files = [int(file.split("_")[1]) for file in os.listdir(result_dir)]
    files = sorted(set(files))

    # iter = st.slider("Select output iteration", 0, len(files), 0)
    iter = st.radio(
        "Iteration:",
        files,
        horizontal=True,
    )

    opencmiss_solution_name = f"BoneOptimisation_{iter}_solution"
    sts.combined_opencmiss_solution_path = os.path.join(
        sts.output_path,
        f"uFE_{opencmiss_solution_name}_combined.vtu",
    )

    if st.button("Combine"):
        with st.spinner("Combining OpenCMISS solution mesh..."):
            result = call_combine_opencmiss_multiblock(
                os.path.join(result_dir, opencmiss_solution_name),
                sts.combined_opencmiss_solution_path,
            )
            if result.returncode:
                st.error("Failed to combine OpenCMISS solution")
                print(result.stderr)
            else:
                st.success("OpenCMISS solution succesfully combined!")


def setup_visualize_opencmiss(
    combined_opencmiss_solution_path,
    clip="y",
    thresh="Structure",
):
    mesh = pv.read(combined_opencmiss_solution_path)
    scalars = list(mesh.cell_data.keys())
    metric = st.radio(
        "Metric:",
        scalars,
        horizontal=True,
    )
    if st.button("Show combined mesh"):
        with st.spinner(
            f"Showing {os.path.basename(combined_opencmiss_solution_path)}..."
        ):
            visualize_opencmiss(
                combined_opencmiss_solution_path,
                metric,
                clip,
                thresh,
            )


def visualize_opencmiss(
    solution_path: str,
    metric: str | None = None,
    clip: str | None = None,
    thresh: str | None = None,
    thresh_val: float = 1.0,
):
    result = call_visualize_opencmiss(
        solution_path,
        metric,
        clip,
        thresh,
        thresh_val,
    )
    if result.returncode:
        st.error("Failed to visualize OpenCMISS results")
        print(result.stderr)


def implicit_domain_volumetric_mesh_opencmiss_solution(
    opencmiss_solution_path,
):
    with st.spinner(
        f"Adaptive remeshing of {os.path.basename(opencmiss_solution_path)}"
    ):
        extract_domain = 3
        opencmiss_adapted_solution_path = (
            os.path.splitext(opencmiss_solution_path)[0] + "_adapted.mesh"
        )
        result = call_implicit_domain_volumetric_mesh_generator(
            opencmiss_solution_path,
            None,
            opencmiss_adapted_solution_path,
            metric="Phi",
            hausd=1e0,
            hgrad=1.3,
            hmin=1e-2,
            hmax=1e0,
            extract_subdomain=extract_domain,
            mem_max=16000,
            refine_iterations=0,
        )

        if extract_domain:
            opencmiss_adapted_solution_path = (
                os.path.splitext(opencmiss_adapted_solution_path)[0] + "_extracted.mesh"
            )

        if result.returncode:
            st.error("Failed adaptive remeshing of OpenCMISS solution mesh")
            print(result.stderr)

        return opencmiss_adapted_solution_path


def clear_session_state(item=None):
    for key in sts.keys():
        if key == "app_path" or key == "output_path":
            continue
        elif item == sts[key]:
            del sts[key]


def clear_output(file_type="all", file_name=None):
    for file in os.listdir(sts.output_path):
        file_path = os.path.join(sts.output_path, file)
        if file_type == "all" or file_type == "files":
            if os.path.isfile(file_path):
                try:
                    os.unlink(file_path)
                    clear_session_state(file_path)
                except Exception as e:
                    print(f"Error while removing file: {e}")
        elif file_type == "file" and file_name is not None:
            if os.path.isfile(file_path) and file == file_name:
                try:
                    os.unlink(file_path)
                    clear_session_state(file_path)
                except Exception as e:
                    print(f"Error while removing file: {e}")
        elif file_type == "all" or file_type == "dirs":
            if os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                    clear_session_state(file_path)
                except Exception as e:
                    print(f"Error while removing directory: {e}")
    st.rerun()
