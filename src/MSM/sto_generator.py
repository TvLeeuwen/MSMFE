# Imports ---------------------------------------------------------------------
import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from pymatreader import read_mat
import plotly.graph_objects as go

from src.MSM.filters import filter_states, filter_states_visualization
from src.MSM.osim_model_parser import parse_model_for_states, parse_model_for_joints

from utils.md_logger import log_md
try:
    from utils.get_paths import md_log_file
except ImportError:
    md_log_file = None


# Parse args ------------------------------------------------------------------
def parse_arguments():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate an initial mesh for mmg based mesh adaptation",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help='Use switches followed by "=" to use CLI file autocomplete, example "-i="',
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Path to input states file (.sto/.mat)",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="Path to input .osim model",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output filename (.sto)",
    )
    parser.add_argument(
        "-f",
        "--filter",
        type=str,
        nargs="+",
        default=None,
        help="String to filter visualized data - can take multiple strings (e.g. -f jointset value)",
    )
    parser.add_argument(
        "-if",
        "--invert_filter",
        action="store_true",
        help="Inverts filter to exclude strings passed with -f / --filter",
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
def read_mat_to_df(input_file):
    data = read_mat(input_file)

    return pd.DataFrame(data["WeightedToes"])


def read_input(input_file, model_file=None):
    """
    Generate .sto based on input file type.

    :param `input_file` Path: Path to input file type used to generate the new .sto
    :: supported file types: .sto / .mat
    """
    df = None
    header = []
    input_file = Path(input_file)
    if input_file.suffix == ".sto":
        with open(input_file, "r") as file:
            header = []
            for line in file:
                header.append(line)
                if "endheader" in line:
                    break
        df = pd.read_csv(input_file, sep="\t", skiprows=len(header))
    elif input_file.suffix == ".mat":

        df2 = read_mat_to_df(input_file)

        print(df2.columns)

        # Set basic header
        header.append("inDegrees=no\n")
        header.append("num_controls=2\n")
        header.append("num_derivatives=0\n")
        header.append("num_input_controls=0\n")
        header.append("num_multipliers=0\n")
        header.append("num_parameters=0\n")
        header.append("num_slacks=0\n")
        header.append("num_states=12\n")
        header.append("DataType=double\n")
        header.append("version=3\n")
        header.append("OpenSimVersion=4.5-2024-07-10-f38669b70\n")
        header.append("endheader\n")

        framerate = 100
        df = pd.DataFrame(0, index=range(len(df2["FrameNumber"])), columns=["time"])
        df["time"] = df2["FrameNumber"] / framerate

        joint_states = parse_model_for_joints(model_file)
        for joint in joint_states:
            print(f"- {joint}")
            for state in joint_states[joint]:
                print(f"-- {state}")
                df[f"/jointset/{joint}/{state}/value"] = df2[f"{joint}Ang"]
                df[f"/jointset/{joint}/{state}/speed"] = df2[f"{joint}Angvel"]
                df[f"/jointset/{joint}/{state}/accel"] = df2[f"{joint}Angacc"]

    return df, header


def write_header(output_file, header):
    with open(output_file, "w") as file:
        file.writelines(header)


def write_columns(df, output_file):
    with open(output_file, "a") as file:
        # Write column names (time + state columns)
        file.write("\t".join(df.columns) + "\n")
        # Write data rows
        for _, row in df.iterrows():
            file.write("\t".join(map(str, row.values)) + "\n")


def visualize_states(df):
    fig = go.Figure()
    for column in df:
        if column != "time":
            fig.add_trace(
                go.Scatter(x=df["time"], y=df[column], mode="lines", name=column)
            )
    fig.update_layout(
        title="Motion Data Visualization",
        xaxis_title="Time (s)",
        yaxis_title="Value",
        legend_title="Variables",
        hovermode="x unified",
    )
    fig.show()


def generate_df_from_model(model_file, df):
    print(f"-- Reading model: {model_file}")
    states = parse_model_for_states(model_file)

    df2 = pd.DataFrame(0, index=range(len(df["time"])), columns=states)
    df2["time"] = df["time"]

    # Hardcoded kinematics filter
    for state in states:
        if "jointset" in state and "flexion" in state:
            print(f" - Writing state: {state}")
            df2[state] = df[state]

    # Get rid of leftover empty matlab lists ([])
    df2 = df2.map(lambda x: 0 if isinstance(x, np.ndarray) and len(x) == 0 else x)
    df2 = df2.map(lambda x: 0.1 if pd.isna(x) else x)

    return df2


# Main ------------------------------------------------------------------------
@log_md(md_log_file)
def generate_sto(
    input_file: Path,
    filter_params: dict | None = None,
    model_file: Path | None = None,
    output_file: Path | None = None,
    visualize=False,
):
    """
    Generate custom .sto for Moco.Track based on filters

    :param input_file Path: .sto or .mat file containing states
    :param filter_params Dict: filter parameters to generate the custom .sto
    :param model_file Path: .osim file, required when generating .sto from .mat.
    :param output_file Path: Custom .sto containing model states, with 0 for non tracked timeseries
    :param visualize Bool: Activate to visualize data contained in generated .sto

    returns: `output_file`: Path to generated .sto
    """
    print("-- Generating kinematics .sto")
    output_file = (
        model_file.with_name(model_file.stem + "_tracked_states.sto")
        if output_file is None and model_file is not None
        else Path(input_file.stem + "_tracked_states.sto")
        if output_file is None and model_file is None and input_file is not None
        else output_file
    )
    filter_params = (
        {
            "state_filters": None,
            "invert_filter": False,
        }
        if filter_params is None
        else filter_params
    )

    if filter_params["state_filters"]:
        df = filter_states(df, filter_params)

    df, header = read_input(input_file, model_file=model_file)

    if input_file.suffix == ".mat":
        if model_file:
            df = generate_df_from_model(model_file, df)
        else:
            sys.exit("Error: .mat file requires .osim model file to generate sto")

    write_header(output_file, header)
    write_columns(df, output_file)

    if visualize:
        visualize_states(df)
        df_filtered = filter_states_visualization(df, filter_params)
        visualize_states(df_filtered)

    print(f"-- Done, writin:\n - {output_file}")

    return output_file


if __name__ == "__main__":
    args = parse_arguments()

    input_file = Path(args.input)
    model_file = Path(args.model) if args.model else None
    output_file = Path(args.output) if args.output else None

    if input_file.parents[0]:
        os.chdir(input_file.parents[0])

    if input_file.suffix == ".mat" and args.model is False:
        sys.exit(
            "Error: .mat file requires .osim model file to generate sto - use the -m flag to add a model Path"
        )

    filter_params = {
        "state_filters": args.filter,
        "invert_filter": args.invert_filter,
    }

    generate_sto(
        input_file,
        filter_params,
        model_file,
        output_file,
        visualize=args.visuals,
    )
