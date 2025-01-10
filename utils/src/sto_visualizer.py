"""
Visualize, animate, and compare .sto files
"""
# Imports ---------------------------------------------------------------------
import os
import argparse
import plotly.graph_objects as go
from src.sto_generator import read_input, filter_states_visualization
from pathlib import Path

from utils.filters import filter_states_visualization

from utils.md_logger import log_md
try:
    from utils.get_paths import md_log_file
except ImportError:
    md_log_file = None


# import manim


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
        "-f",
        "--filter",
        type=str,
        nargs="+",
        default=None,
        help="Strings to filter visualized data (e.g. jointset angle)- filters out states containing any of the passed filter"
    )
    parser.add_argument(
        "-if",
        "--invert_filter",
        action="store_true",
        help="Inverts filter to exclude strings passed with -f / --filter",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
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


# Main ------------------------------------------------------------------------
@log_md(md_log_file)
def visualize_sto(input_file, filter_params):
    df, _ = read_input(input_file)

    if filter_params["state_filters"]:
        df = filter_states_visualization(df, filter_params)

    visualize_states(df)


if __name__ == "__main__":
    args = parse_arguments()

    input_file = Path(args.input)

    if input_file.parents[0]:
        os.chdir(input_file.parents[0])

    filter_params = {}
    filter_params["state_filters"] = args.filter
    filter_params["invert_filter"] = args.invert_filter
    print(filter_params)

    visualize_sto(
        input_file,
        filter_params,
    )
