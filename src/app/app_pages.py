# Imports ---------------------------------------------------------------------
import os
import streamlit as st
from src.app.app_io import (
    project_uploader,
    osim_uploader,
    kine_uploader,
    geom_uploader,
    dir_downloader,
)
from src.app.app_functions import (
    generate_kinematics,
    track_kinematics,
    force_vector_extraction,
    toi_selector,
    bone_muscle_extraction,
    manual_BC_selector,
    visualize_BCs,
    remesh_surface,
    generate_volumetric_mesh,
    clear_output,
)
from src.app.app_visuals import (
    visual_compare_timeseries,
    visual_muscle_data,
    visual_force_vector_gif,
    visual_toi_boi_force_vectors,
    visual_BCs,
)

sts = st.session_state


# Defs ------------------------------------------------------------------------
def page_home():
    st.title("Input")
    st.write(f"Home directory: {sts.app_path}")

    st.subheader("Load previous project files")
    project_uploader()

    st.divider()
    st.subheader("Model file")
    osim_uploader()
    st.subheader("Geometry files")
    geom_uploader()
    st.subheader("Kinematics file")
    kine_uploader()

    with st.expander("Debug: Show states", expanded=False):
        st.write(sts)


def page_track_kinematics():
    st.title("Kinematic tracking")

    if (
        sts.osim_path is not None
        and sts.kine_path is not None
        and os.path.exists(sts.osim_path)
        and os.path.exists(sts.kine_path)
    ):
        st.write(f"Model: {os.path.basename(sts.osim_path)}")
        if st.button("Generate kinematics"):
            generate_kinematics(
                sts.osim_path,
                sts.kine_path,
                sts.output_path,
            )

        if sts.kinematics_path is not None and os.path.exists(sts.kinematics_path):
            if st.button("Track kinematics"):
                track_kinematics(
                    sts.app_path,
                    sts.osim_path,
                    sts.output_path,
                )

    else:
        st.write("No files uploaded yet. Please upload under :rainbow[input]")

    # Compare kinematics ------------------------------------------------------
    if (
        sts.kinematics_path is not None
        and os.path.exists(sts.kinematics_path)
        and sts.moco_solution_path is not None
        and os.path.exists(sts.moco_solution_path)
    ):
        st.subheader("Kinematics: Validate output versus input")

        group_kine = st.toggle("Group kinematics legend", value=True)
        visual_compare_timeseries(
            sts.kinematics_path,
            sts.moco_solution_path,
            group_kine,
        )

    # Validate muscle parameters ----------------------------------------------
    if sts.moco_solution_muscle_fiber_path is not None and os.path.exists(
        sts.moco_solution_muscle_fiber_path
    ):
        st.subheader("Dynamics: Muscle fiber parameters")

        group_legend = st.toggle("Group dynamics legend", value=True)
        visual_muscle_data(
            sts.moco_solution_muscle_fiber_path,
            group_legend,
        )


def page_force_vector():
    st.header("Force vector extraction")

    if sts.osim_path is not None and os.path.exists(sts.osim_path):
        st.write(f"Model selected: {os.path.basename(sts.osim_path)}")

        # Boi selector -----------------------------------------------------------
        sts.bones_muscle_map = bone_muscle_extraction(sts.osim_path)
        bones = [bones for bones in sts.bones_muscle_map]
        boi = st.radio(
            "Bone of interest:",
            [bone for bone in bones],
            index=None,
        )
        if boi:
            sts.boi = boi

        if sts.boi:
            file_mapping = {
                ".gif": "gif_path",
                "origins.json": "force_origins_path",
                "vectors.json": "force_vectors_path",
                "volumetric.mesh": "vol_path",
                "extracted.mesh": "vol_path",
            }
            for dirpath, _, files in os.walk(sts.output_path):
                for file in files:
                    if sts.boi in file:
                        for key, attr in file_mapping.items():
                            if key in file:
                                setattr(sts, attr, os.path.join(dirpath, file))
                                break

                    # if sts.boi in file:
                    #     if ".gif" in file:
                    #         sts.gif_path = os.path.join(dirpath, file)
                    #     elif "origins.json" in file:
                    #         sts.force_origins_path = os.path.join(dirpath, file)
                    #     elif "vectors.json" in file:
                    #         sts.force_vectors_path = os.path.join(dirpath, file)
                    #     elif "volumetric.mesh" in file:
                    #         sts.vol_path = os.path.join(dirpath, file)

    else:
        st.write("No files uploaded yet. Please upload under :rainbow[input]")

    if sts.osim_path is not None and sts.moco_solution_path is not None:
        force_vector_extraction(
            sts.osim_path,
            sts.moco_solution_path,
            sts.boi,
            sts.output_path,
        )
    else:
        st.write(
            "No dynamics detected. Run :rainbow[Track Kinematics] \
                before extracting force vectors"
        )

    if (
        sts.boi is not None
        and sts.geom_path is not None
        and os.path.exists(sts.geom_path)
    ):
        for _, _, bones in os.walk(sts.geom_path):
            for bone in bones:
                if sts.boi in bone:
                    sts.boi_path = os.path.join(
                        sts.geom_path,
                        bone,
                    )

    else:
        st.write("No geometry files uploaded yet. Please upload under :rainbow[Input]")

    if (
        sts.force_origins_path is not None
        and sts.force_vectors_path is not None
        and os.path.exists(sts.force_origins_path)
        and os.path.exists(sts.force_vectors_path)
        and sts.boi_path is not None
    ):
        # Generate gif ----------------------------------------------------
        if st.button(f"Generate {sts.boi} gif"):
            visual_force_vector_gif(
                sts.boi_path,
                sts.moco_solution_muscle_fiber_path,
                sts.force_origins_path,
                sts.force_vectors_path,
                sts.output_path,
            )

    if (
        sts.gif_path is not None
        and os.path.exists(sts.gif_path)
        and sts.boi is not None
        and sts.boi in sts.gif_path
    ):
        st.image(
            sts.gif_path,
            caption="Force vector over time",
        )


def page_meshing():
    st.title(f"Volumetric meshing")

    select_mesh_toggle = st.toggle("Mesh OpenSim geometry", value=True)

    if not select_mesh_toggle:
        st.write("Upload custom geometry")

    if sts.boi is not None and sts.boi_path is not None:
        # if st.button("Remesh surface mesh"):
        #     result = remesh_surface(
        #         sts.boi_path,
        #         sts.output_path,
        #     )
        #     if result.returncode:
        #         st.error("Failed to remesh")
        #         print(result.stderr)

        if st.button(f"Generate {sts.boi} volumetric mesh"):
            result, sts.vol_path = generate_volumetric_mesh(
                sts.boi_path,
                sts.output_path,
                1,
            )
            if result.returncode:
                st.error("Failed to generate mesh")
                print(result.stderr)

        if os.path.exists(sts.vol_path) and sts.boi in sts.vol_path:
            st.success(f"Volumetric {sts.boi} mesh generated")

    else:
        st.write(f"Please select a bone of interest under :rainbow[Muscle forces]")


def page_BCs():
    st.title("Boundary Conditions")

    select_BC_toggle = st.toggle("OpenSim derived BC selection", value=True)

    if select_BC_toggle:
        if sts.boi is not None:
            if sts.moco_solution_muscle_fiber_path is not None and os.path.exists(
                sts.moco_solution_muscle_fiber_path
            ):
                st.subheader(f"Select time of interest - {sts.boi}")
                muscles = [muscle for muscle in sts.bones_muscle_map[sts.boi]]

                toi_selector(
                    sts.moco_solution_muscle_fiber_path,
                    muscles,
                )
                st.write(f"Selected time: {st.session_state.toi}")
            else:
                st.write("No dynamics detected. Please run :rainbow[Track Kinematics]")
        else:
            st.write(f"Please select a bone of interest under :rainbow[Muscle forces]")

        if sts.toi:
            with st.empty():
                visual_toi_boi_force_vectors(
                    sts.boi_path,
                    sts.moco_solution_muscle_fiber_path,
                    sts.force_origins_path,
                    sts.force_vectors_path,
                    sts.toi,
                )

    else:
        st.subheader(f"Manual BC selection")

        if os.path.exists(sts.vol_path) and sts.boi in sts.vol_path:
            st.write(os.path.basename(sts.vol_path))
            if st.button(f"Select BCs on {sts.boi}"):
                manual_BC_selector(
                    sts.vol_path,
                    os.path.splitext(sts.osim_path)[0] + "_" + sts.boi,
                )

        else:
            st.write(
                "Generate a volumetric mesh under :rainbow[Volumetric meshing] \
                    before selecting any boundary conditions"
            )

    if sts.dirichlet_path:
        st.divider()
        if st.button(f"Show current BCs for {sts.boi}"):

            visualize_BCs(
                    sts.vol_path,
                    sts.dirichlet_path,
                    sts.neumann_path,
                )


def page_FE():
    st.title("Finite Element")

    if sts.dirichlet_path:
        if st.button("Show BCs"):
            visual_BCs(
                sts.vol_path,
                sts.dirichlet_path,
                sts.neumann_path,
            )
        st.divider()


def page_output():
    st.title("Output")
    st.write(f"Output directory: {sts.output_path}")

    output_files = [
        f
        for f in sorted(os.listdir(sts.output_path), key=lambda x: (x.lower(), len(x)))
        if os.path.isfile(os.path.join(sts.output_path, f))
    ]

    if output_files:
        download = "model" if sts.osim_path is not None else "dir"
        dir_downloader(
            sts.output_path,
            "Output",
            download_name=download,
        )

        if st.button(":red[Clear all output]"):
            clear_output("all")
            st.rerun()

        st.subheader("Files")
        if st.button(":red[Clear files]"):
            clear_output("files")

        st.subheader("Download files")

        for file_name in output_files:
            with open(os.path.join(sts.output_path, file_name), "rb") as file:
                file_data = file.read()
                st.download_button(
                    label=f"{file_name}",
                    data=file_data,
                    file_name=file_name,
                )

        st.subheader("Remove files", divider="red")
        for file_name in output_files:
            if st.button(f":red[{file_name}]"):
                clear_output("file", file_name)

        st.subheader("Folders")
        if st.button(":red[Clear folders]"):
            clear_output("dirs")

        [
            dir_downloader(os.path.join(sts.output_path, dir), dir, show_files=True)
            for dir in os.listdir(sts.output_path)
            if os.path.isdir(os.path.join(sts.output_path, dir))
        ]

    else:
        st.write("Output folder is empty")
