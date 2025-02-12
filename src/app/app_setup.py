import os
from src.app.app_pages import *


def setup_app():
    pages = {
        "Home": [
            st.Page(page_home, title="Input"),
        ],
        "MSM": [
            st.Page(page_kinematics, title="Kinematics"),
            st.Page(page_dynamics, title="Dynamics"),
        ],
        "FE": [
            st.Page(page_boi, title="Bone of interest"),
            st.Page(page_meshing, title="Meshing"),
            st.Page(page_BCs, title="Boundary conditions"),
            st.Page(page_FE, title="Finite Element"),
            st.Page(page_viewFE, title="Result"),
        ],
        "Output": [
            st.Page(page_output, title="Output"),
        ],
    }

    pg = st.navigation(pages)

    if st.sidebar.button("Stop server"):
        os._exit(0)

    return pg
