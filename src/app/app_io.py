"""Functions to facilitate file I/O"""

# Imports ---------------------------------------------------------------------
import os
import io
import zipfile
import streamlit as st

from src.MSM.sto_generator import read_mat_to_df
sts = st.session_state


# Defs ------------------------------------------------------------------------
def setup_paths():
    # Folders -----------------------------------------------------------------
    if "app_path" not in sts:
        sts.app_path = os.getcwd()

    if "output_path" not in sts:
        sts.output_path = os.path.join(sts.app_path, "app/output")

    if "example_path" not in sts:
        sts.example_path = os.path.join(sts.app_path, "app/example")

    # Files -------------------------------------------------------------------
    if "osim_path" not in sts or sts.osim_path is None:
        sts.osim_path = find_file_in_dir(
            sts.output_path,
            ".osim",
        )

    if "geom_path" not in sts:
        sts.geom_path = find_file_in_dir(
            sts.output_path,
            "Geometry",
        )

    if "kine_path" not in sts or sts.kine_path is None:
        sts.kine_path = find_file_in_dir(
            sts.output_path,
            ".mat",
        )

    if "kinematics_path" not in sts or sts.kinematics_path is None:
        sts.kinematics_path = find_file_in_dir(
            sts.output_path,
            "tracked_states.sto",
        )

    if "moco_solution_path" not in sts or sts.moco_solution_path is None:
        sts.moco_solution_path = find_file_in_dir(
            sts.output_path,
            "success.sto",
        )

    if (
        "moco_solution_muscle_fiber_path" not in sts
        or sts.moco_solution_muscle_fiber_path is None
    ):
        sts.moco_solution_muscle_fiber_path = find_file_in_dir(
            sts.output_path,
            "muscle_fiber_data.sto",
        )

    if "force_origins_path" not in sts or sts.force_origins_path is None:
        sts.force_origins_path = find_file_in_dir(
            sts.output_path,
            "muscle_origins.json",
        )

    if "force_vectors_path" not in sts or sts.force_vectors_path is None:
        sts.force_vectors_path = find_file_in_dir(
            sts.output_path,
            "muscle_vectors.json",
        )

    if "gif_path" not in sts or sts.gif_path is None:
        sts.gif_path = find_file_in_dir(
            sts.output_path,
            "vectors.gif",
        )

    if "vol_path" not in sts or sts.vol_path is None:
        sts.vol_path = find_file_in_dir(
            sts.output_path,
            "extracted.mesh",
        )

    if "dirichlet_path" not in sts or sts.dirichlet_path is None:
        sts.dirichlet_path = find_file_in_dir(
            sts.output_path,
            "dirichlet_BC.npy",
        )

    if "neumann_path" not in sts or sts.neumann_path is None:
        sts.neumann_path = find_file_in_dir(
            sts.output_path,
            "neumann_BC.npy",
        )


    # Params ------------------------------------------------------------------
    if "boi" not in sts:
        sts.boi = None
    if "toi" not in sts:
        sts.toi = None

    # Keep dir on homedir on refresh - may get stuck in /output
    if os.getcwd() == sts.app_path:
        os.makedirs(sts.output_path, exist_ok=True)
    elif os.getcwd() == sts.output_path:
        os.chdir(sts.app_path)


def find_file_in_dir(directory, string):
    for root, _, files in os.walk(directory):
        f = 0
        for file in files:
            if string == ".osim":
                if ".osim" in file:
                    f += 1
                    if f > 1:
                        print("Multiple .osim files detected. Autoselected None...")
                        return None

                    osim_file = os.path.join(root, file)
                    return osim_file if osim_file else None
            else:
                if string in file.lower():
                    return os.path.join(directory, file)


def write_to_output(file, output_dir, tag):
    tag = None if file.name[0: len(tag)] == tag else tag
    file_name = f"{tag}_{file.name}" if tag else file.name
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())

    return file_path


def osim_uploader():
    osim_ref = st.file_uploader(
        "Drag and drop OR select .osim model here",
        type=["osim"],
    )
    if osim_ref is not None:
        sts.osim_path = write_to_output(
            osim_ref,
            sts.output_path,
            "MSM",
        )


def project_uploader():
    output_path = st.file_uploader(
        "Drag and drop OR select all previous output files here",
        accept_multiple_files=True,
        type=[".osim", ".sto", ".json", ".gif", ".mat"],
    )
    if output_path is not None:
        if os.path.exists(sts.output_path):
            for output in output_path:
                write_to_output(
                    output,
                    sts.output_path,
                    "",
                )
        setup_paths()


def geom_uploader():
    geom_path = st.file_uploader(
        "Drag and drop OR select all Geometry files here",
        accept_multiple_files=True,
        type=[".vtp"],
    )
    if geom_path is not None:
        sts.geom_path = os.path.join(sts.output_path, "Geometry")
        if not os.path.exists(sts.geom_path) and len(geom_path) != 0:
            os.mkdir(sts.geom_path)
        if os.path.exists(sts.geom_path):
            for geom_ref in geom_path:
                write_to_output(
                    geom_ref,
                    sts.geom_path,
                    "",
                )


def kine_uploader():
    kine_path = st.file_uploader(
        "Drag and drop OR select kinematics file here", type=[".mat", ".sto"]
    )
    if kine_path is not None:
        sts.kine_path = write_to_output(
            kine_path,
            sts.output_path,
            "MSM",
        )

    if sts.kine_path is not None and os.path.exists(sts.kine_path):
        with st.expander("Show .mat keyvalues", expanded=False):
            df = read_mat_to_df(sts.kine_path)
            st.write([col[:-3] for col in df if col.endswith("Ang")])


def zip_directory(folder_path):
    """Compress an entire directory into a ZIP file in memory."""
    buffer = io.BytesIO()  # Create a buffer to hold the ZIP file
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Add file to the ZIP archive with a relative path
                arcname = os.path.relpath(file_path, start=folder_path)
                zip_file.write(file_path, arcname=arcname)
    buffer.seek(0)  # Move to the start of the buffer
    return buffer.getvalue()


def dir_downloader(dir, dir_name, show_files=False, download_name="dir"):
    if os.path.exists(dir):
        download = (
            os.path.splitext(os.path.basename(sts.osim_path))[0]
            if download_name == "model"
            else dir_name
        )
        st.download_button(
            label=f"Download {dir_name}.zip",
            data=zip_directory(dir),
            file_name=f"{download}.zip",
            mime="application/zip",
        )
        if show_files:
            st.write([file for file in os.listdir(dir)])
    else:
        st.error("The specified folder does not exist. Please check the path.")
