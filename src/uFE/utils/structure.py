"""
Modules for standardizing project file and dir structure.
"""
import os
from pathlib import Path


def check_project_directory(project_path: Path, verbose=False):
    if project_path.exists() and project_path.is_dir():
        if verbose:
            print(f"-- Directory found: '{project_path.name}' ")
    else:
        os.mkdir(project_path)
        if verbose:
            print(f"-- Directory does not exist:\n - Dir: '{project_path.name}' created")
