"""Conda environment setup for MSMFE
-- Run this script in the main MSMFE repo folder without any active conda envs:
 - conda deactivate
 - python install_envMSMFE.py
This script installs or updates two conda environments for MSMFE:
-- envMSMFE: main env that is activated by the user to run the MSMFE app.
-- envMSM_FE: called by MSMFE functions in the backgroud to run FE functionality
"""

# Imports ---------------------------------------------------------------------
import os
import textwrap
import subprocess

envs = ["envMSMFE", "envMSM_FE"]

for env in envs:
    # Check for existing envs - remove them for fresh install
    try:
        result = subprocess.run(
            ["conda", "env", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if env in result.stdout:
            try:
                subprocess.run(["conda", "remove", "-n", env, "--all", "--y"])
            except Exception as e:
                print(f"Error removing {env}: {e}")
                os._exit(0)

    except Exception as e:
        print(f"Error checking Conda environments: {e}")

    # Install envMSMFE - requires opensim conda install before dependencies or osim will break
    try:
        subprocess.run(
            ["conda", "env", "create", "-f", f"setup_envMSMFE/{env}.yml"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error installing {envs[0]}:\n {e}")
        os._exit(0)

    if os.path.isfile(f"setup_envMSMFE/{env}_requirements.txt"):
        print(
            f"Installing {env} dependencies, "
            "this may take some time depending on your system..."
        )
        try:
            subprocess.run(
                [
                    "conda",
                    "run",
                    "-n",
                    f"{env}",
                    "pip",
                    "install",
                    "-r",
                    f"setup_envMSMFE/{env}_requirements.txt",
                ],
                check=True,
            )

        except subprocess.CalledProcessError as e:
            print(f"Error during pip installation: {e}")

print(
    textwrap.dedent(
        """
#
# Conda envMSMFE installed. To activate this environment, use
#
#     $ conda activate envMSMFE
#
# To deactivate an active environment, use
#
#     $ conda deactivate
#
# To uninstall this environment, use
#
#     $ conda remove -n envMSMFE --all
#
"""
    )
)
