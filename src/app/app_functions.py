"""Streamlit app function widgets calling src files"""

# Imports ---------------------------------------------------------------------
import os
import shutil
import streamlit as st
from pathlib import Path

from src.sto_generator import generate_sto
from src.moco_track_kinematics import moco_track_states
from src.force_vector_extractor import extract_force_vectors, extract_model_bones


# Defs ------------------------------------------------------------------------
def run_moco(moco_path, osim_path, output_path):
    try:
        os.chdir(output_path)
        filter_params = {
            "state_filters": ["jointset"],
            "invert_filter": False,
        }

        print(osim_path)
        print(st.session_state.kinematics_path)

        solution_path, muscle_fiber_path = moco_track_states(
            Path(osim_path),
            Path(st.session_state.kinematics_path),
            filter_params,
        )
        os.chdir(moco_path)

        st.session_state.moco_solution_path = os.path.join(
            output_path, str(solution_path)
        )

        st.session_state.moco_solution_muscle_fiber_path = os.path.join(
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
        st.session_state.kinematics_path = os.path.join(
            output_path, str(kinematics_path)
        )
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
    bone_muscle_map = extract_model_bones(model)

    return bone_muscle_map


def force_vector_extraction(model, sto_data, boi, output_path):
    if st.button("Extract force vectors"):
        with st.spinner("Extracting vectors"):
            try:
                (
                    st.session_state.force_origins_path,
                    st.session_state.force_vectors_path,
                ) = extract_force_vectors(model, sto_data, boi, output_path)

            except Exception as e:
                st.error(f"An error occurred: {e}")
            st.success(f"Extraction: {boi} succesful")


def clear_session_state():
    for key in st.session_state.keys():
        if key == "app_path" or key == "output_path":
            continue
        else:
            del st.session_state[key]
    st.rerun()


def clear_output(filetype="all"):
    for file in os.listdir(st.session_state.output_path):
        file_path = os.path.join(st.session_state.output_path, file)
        if filetype == "all" or filetype == "files":
            if os.path.isfile(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Error while removing file: {e}")
        elif filetype == "all" or filetype == "dirs":
            if os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error while removing directory: {e}")
    clear_session_state()
