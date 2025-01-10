"""Streamlit app function widgets calling src files"""

# Imports ---------------------------------------------------------------------
import os
import streamlit as st
from pathlib import Path

from src.sto_generator import generate_sto
from src.moco_track_kinematics import moco_track_states
from src.force_vector_extractor import extract_force_vectors
from src.bone_muscle_extractor import extract_muscle_and_bone


# Defs ------------------------------------------------------------------------

# MSM -------------------------------------------------------------------------
def run_moco(moco_path, osim_path, mat_path, output_path):
    if st.button("Track kinematics"):
        try:
            os.chdir(output_path)
            filter_params = {
                "state_filters": ["jointset"],
                "invert_filter": False,
            }

            st.session_state.kinematics_path = generate_sto(
                Path(mat_path),
                model_file=Path(osim_path),
            )
            st.session_state.kinematics_path = os.path.join(
                output_path, str(st.session_state.kinematics_path)
            )
            st.write(f"Kinematics written: {st.session_state.kinematics_path}")
            st.write("Running Moco.Track kinematics...")

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

            st.success("Script executed successfully!")
            st.write(f"Solution written: {st.session_state.moco_solution_path}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            os.chdir(moco_path)


def bone_muscle_extraction(model):
    bone_muscle_map = extract_muscle_and_bone(model)

    return bone_muscle_map



def force_vector_extraction(model, sto_data, output_path):
    if st.button("Extract force vectors"):
        try:
            (
                st.session_state.force_origins_path,
                st.session_state.force_vectors_path,
            ) = extract_force_vectors(model, sto_data, output_path)

        except Exception as e:
            st.error(f"An error occurred: {e}")
