# Imports ---------------------------------------------------------------------
import os
import streamlit as st
from app.widgets.app_io import (
    osim_uploader,
    kine_uploader,
    geom_uploader,
    find_file_in_dir,
    dir_downloader,
)
from app.widgets.app_functions import (
    track_kinematics,
    force_vector_extraction,
    bone_muscle_extraction,
    clear_output,
)
from app.widgets.app_visuals import (
    visual_compare_timeseries,
    visual_validate_muscle_parameters,
    visual_force_vector_gif,
)


# Defs ------------------------------------------------------------------------
def page_home():
    st.title("Input")
    st.write(f"Home directory: {st.session_state.app_path}")

    osim_uploader()
    geom_uploader()
    kine_uploader()

    st.write(st.session_state)


def page_track_kinematics():
    st.title("Kinematic tracking")

    if (
        st.session_state.osim_path is not None
        and st.session_state.kine_path is not None
        and os.path.exists(st.session_state.osim_path)
        and os.path.exists(st.session_state.kine_path)
    ):
        with st.spinner("Tracking kinematics..."):
            track_kinematics(
                st.session_state.app_path,
                st.session_state.osim_path,
                st.session_state.kine_path,
                st.session_state.output_path,
            )
    else:
        st.write("No files uploaded yet. Please upload under :rainbow[input]")

    # Compare kinematics ------------------------------------------------------
    if (
        st.session_state.kinematics_path is not None
        and os.path.exists(st.session_state.kinematics_path)
        and st.session_state.moco_solution_path is not None
        and os.path.exists(st.session_state.moco_solution_path)
    ):
        st.subheader("Kinematics: Validate output versus input")

        visual_compare_timeseries(
            st.session_state.kinematics_path,
            st.session_state.moco_solution_path,
        )

    # Validate muscle parameters ----------------------------------------------
    if st.session_state.moco_solution_muscle_fiber_path is not None and os.path.exists(
        st.session_state.moco_solution_muscle_fiber_path
    ):
        st.subheader("Dynamics: Muscle fiber parameters")

        visual_validate_muscle_parameters(
            st.session_state.moco_solution_muscle_fiber_path,
        )


def page_force_vector():
    st.header("Force vector extraction")

    if st.session_state.osim_path is not None and os.path.exists(
        st.session_state.osim_path
    ):
        st.write(f"Model selected: {os.path.basename(st.session_state.osim_path)}")
    else:
        st.write("No files uploaded yet. Please upload under :rainbow[input]")

    # Bone selector -----------------------------------------------------------
    if st.session_state.osim_path is not None and os.path.exists(
        st.session_state.osim_path
    ):
        bones = bone_muscle_extraction(st.session_state.osim_path)
        boi = st.radio(
            "Bone of interest:",
            [bone for bone in bones],
            index=None,
        )
        st.write("Selected:", boi)
        st.session_state.boi_path = os.path.join(
            st.session_state.example_path, f"Geometry/{boi}.vtp"
        )

        if "force_origins_path" not in st.session_state:
            st.session_state.force_origins_path = find_file_in_dir(
                st.session_state.output_path,
                f"{boi}_muscle_origins.json",
            )
        if "force_vectors_path" not in st.session_state:
            st.session_state.force_vectors_path = find_file_in_dir(
                st.session_state.output_path,
                f"{boi}_muscle_vectors.json",
            )

    if (
        st.session_state.osim_path is not None
        and st.session_state.moco_solution_path is not None
        and boi is not None
    ):
        force_vector_extraction(
            st.session_state.osim_path,
            st.session_state.moco_solution_path,
            boi,
            st.session_state.output_path,
        )
    elif boi is None:
        pass
    else:
        st.write(
            "No dynamics detected. Run :rainbow[Track Kinematics] \
                before extracting force vectors"
        )

    st.write(st.session_state.moco_solution_path)

    if (
        st.session_state.force_origins_path is not None
        and st.session_state.force_vectors_path is not None
        and os.path.exists(st.session_state.force_origins_path)
        and os.path.exists(st.session_state.force_vectors_path)
        and boi is not None
    ):
        if st.button("Generate gif"):
            visual_force_vector_gif(
                st.session_state.boi_path,
                st.session_state.moco_solution_path,
                st.session_state.force_origins_path,
                st.session_state.force_vectors_path,
                st.session_state.output_path,
            )

    if st.session_state.gif_path is not None and os.path.isfile(
        st.session_state.gif_path,
    ):
        st.image(
            st.session_state.gif_path,
            caption="Force vector over time",
        )


def page_FE():
    st.title("Finite Element")

    if st.button("Generate volumetric bone mesh"):
        pass


def page_output():
    st.title("Output")
    st.write(f"Output directory: {st.session_state.output_path}")

    output_files = [
        f
        for f in os.listdir(st.session_state.output_path)
        if os.path.isfile(os.path.join(st.session_state.output_path, f))
    ]

    if output_files:
        st.subheader("Files")
        for file_name in output_files:
            with open(
                os.path.join(st.session_state.output_path, file_name), "rb"
            ) as file:
                file_data = file.read()
                st.download_button(
                    label=f"{file_name}",
                    data=file_data,
                    file_name=file_name,
                )
        [
            dir_downloader(os.path.join(st.session_state.output_path, dir), dir)
            for dir in os.listdir(st.session_state.output_path)
            if os.path.isdir(os.path.join(st.session_state.output_path, dir))
        ]

        st.subheader("Clear output")
        if st.button("Clear all output"):
            clear_output()
            st.rerun()

    else:
        st.write("Output folder is empty")
