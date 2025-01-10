"""Conda environment setup for MSMFE"""

# Imports ---------------------------------------------------------------------
import subprocess
import os
import textwrap

# Check for existing envMSMFE
try:
    result = subprocess.run(["conda", "env", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if 'envMSMFE' in result.stdout:
        try:
            subprocess.run(["conda", "remove", "-n", "envMSMFE", "--all", "--y"])
        except Exception as e:
            print(f"Error removing envMSMFE: {e}")
            os._exit(0)

except Exception as e:
    print(f"Error checking Conda environments: {e}")

try:
    subprocess.run(
        ["conda", "env", "create", "-f", "setup_envMSMFE/envMSMFE.yml"],
        check=True,
    )
except subprocess.CalledProcessError as e:
    print(f"Error installing envMSMFE:\n {e}")
    os._exit(0)

print("Installing dependencies, this may take some time depending on your system...")

try:
    subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "envMSMFE",
            "pip",
            "install",
            "-r",
            "setup_envMSMFE/requirements.txt",
        ],
        check=True,
    )

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

except subprocess.CalledProcessError as e:
    print(f"Error during pip installation: {e}")
