import os
from src.app.app_pages import *


def setup_app():
    pages = {
        "MSM": [
            st.Page(page_home, title="Input"),
            st.Page(page_track_kinematics, title="Track kinematics"),
            st.Page(page_force_vector, title="Muscle forces"),
        ],
        "FE": [
            st.Page(page_meshing, title="Volumetric meshing"),
            st.Page(page_BCs, title="Boundary conditions"),
            st.Page(page_FE, title="Finite Element"),
        ],
        "Output": [
            st.Page(page_output, title="Output"),
        ],
    }

    pg = st.navigation(pages)

    if st.sidebar.button("Stop server"):
        os._exit(0)

    return pg
