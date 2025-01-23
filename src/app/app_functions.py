"""Streamlit app function widgets calling src files"""

# Imports ---------------------------------------------------------------------
import os
import shutil
import pandas as pd
import streamlit as st
from pathlib import Path

from src.MSM.sto_generator import generate_sto, read_input
from src.MSM.moco_track_kinematics import moco_track_states
from src.MSM.force_vector_extractor import (
    extract_force_vectors,
    extract_model_bone_and_muscle,
)
from src.app.app_visuals import click_visual_toi_selector

sts = st.session_state

# Defs ------------------------------------------------------------------------
def run_moco(moco_path, osim_path, output_path):
    try:
        os.chdir(output_path)
        filter_params = {
            "state_filters": ["jointset"],
            "invert_filter": False,
        }
        solution_path, muscle_fiber_path = moco_track_states(
            Path(osim_path),
            Path(sts.kinematics_path),
            filter_params,
        )
        os.chdir(moco_path)

        sts.moco_solution_path = os.path.join(
            output_path, str(solution_path)
        )

        sts.moco_solution_muscle_fiber_path = os.path.join(
            output_path, str(muscle_fiber_path)
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
        os.chdir(moco_path)


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


def bone_muscle_extraction(model):
    bone_muscle_map = extract_model_bone_and_muscle(model)

    return bone_muscle_map


# Muscle forces ---------------------------------------------------------------
def force_vector_extraction(model, sto_data, boi, output_path):
    if st.button(f"Extract {boi} force vectors"):
        with st.spinner("Extracting vectors"):
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


def clear_session_state():
    for key in sts.keys():
        if key == "app_path" or key == "output_path":
            continue
        else:
            del sts[key]
    st.rerun()


def clear_output(file_type="all", file_name=None):
    for file in os.listdir(sts.output_path):
        file_path = os.path.join(sts.output_path, file)
        if file_type == "all" or file_type == "files":
            if os.path.isfile(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Error while removing file: {e}")
        elif file_type == "file" and file_name is not None:
            if os.path.isfile(file_path) and file == file_name:
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Error while removing file: {e}")
        elif file_type == "all" or file_type == "dirs":
            if os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error while removing directory: {e}")
    clear_session_state()
