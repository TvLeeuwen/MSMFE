"""Some methods to deal with opensim not being found or installed"""

# Imports ---------------------------------------------------------------------
import site
import os
import sys


# Defs ------------------------------------------------------------------------
def import_opensim():
    # Get the site-packages directory for the current environment
    site_packages_dirs = site.getsitepackages()

    # Locate the opensim package folder
    opensim_path = None
    for dir in site_packages_dirs:
        potential_path = os.path.join(dir, "Lib/opensim")
        if os.path.exists(potential_path):
            opensim_path = potential_path
            print(f"{opensim_path} found!")
            break
    if opensim_path:
        try:
            sys.path.insert(0, opensim_path)
            print("Adding osim to Path")
            import opensim as osim

            return osim
        except ImportError as e:
            print("Error importing OpenSim after installation:", e)
    else:
        try:
            import opensim as osim

            return osim
        except ImportError as e:
            print("Error importing OpenSim after installation:", e)
