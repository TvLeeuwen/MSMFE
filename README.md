# MSMFE
## Install dependencies

### Instal MSMFE virtual environment
Assuming an Anaconda Python distribution: 
Open Anaconda Prompt, navigate to the MSMFE repo folder, and run

    python install_envMSMFE.py

If Anaconda is not installed, install Anaconda.

## Activate MSMFE

    conda activate envMSMFE

## Update envMSMFE
Make sure envMSMFE is not active, if it is run

    conda deactivate

Rerun the installer script by running

    python install_envMSMFE.py

## MSMFE app

### Run MSMFE.track kinematics
Run the MSMFE track app using 

    streamlit run MSMFE_app.py

Select or drag and drop the model / kinematics you want to run track.

Press the `Run MSMFE` button

## Manual conda env install

### Create env

    conda create -n envMSMFE python=3.10

### Activate 

    conda activate envMSMFE

### Install dependencies (opensim first)

    conda install -c opensim-org openssim

    pip install pandas pymatreader plotly lxml streamlit pyvista stpyvista imageio
    
    MSM_FE:
    numpy pyvista tetgen meshio trimesh

### Remove env
    
    conda remove -n envMSMFE --all
