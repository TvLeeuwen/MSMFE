""""
MocoTrack Emu State tracking:
Tracks kinematic states predicted by the Dromaius_model_v4_intermed.osim model
Optimizes non-kinematics states for close correspondence to predicted kinematics
    by Timo van Leeuwen
Based on:
OpenSim Moco: exampleMocoTrack.py
    by Nicholas Bianco
    Copyright (c) 2023 Stanford University and the Authors
Input model and kinematics generated by:
    Emu model build and published by van Bijlert - doi: 10.1126/sciadv.ado0936
    Prediction script in Matlab by Pacha van Bijlert
        adapted for Python by Timo van Leeuwen
"""


# Imports ---------------------------------------------------------------------
import os
import sys
import argparse
from pathlib import Path

from setup_envMSMFE.osim_path import import_opensim

osim = import_opensim()

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
        "-m",
        "--model",
        type=str,
        help="Path to input .osim model",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--sto",
        type=str,
        help="Path to input .sto file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Filename for output .sto file",
    )
    parser.add_argument(
        "-f",
        "--filter",
        type=str,
        nargs="+",
        default=None,
        help="Strings to filter visualized data (e.g. jointset angle)- filters out states containing any of the passed filter",
    )
    parser.add_argument(
        "-if",
        "--invert_filter",
        action="store_true",
        help="Inverts filter to exclude strings passed with -f / --filter",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
def set_state_weights(
    track,
    state_names,
    state_weights,
    filters,
    inverse_filter=False,
    verbose=False,
):
    tracked_states = 0
    # Set weights based on filters and inverse_filter flag
    for state_name in state_names:
        if filters:
            weight = (
                10 if (any(f in state_name for f in filters) != inverse_filter) else 0
            )
        else:
            weight = 10
        state_weights.cloneAndAppend(osim.MocoWeight(state_name, weight))
        if weight:
            tracked_states += 1
            print(f"Tracking: {state_name}")
    track.set_states_weight_set(state_weights)
    print(f"-- Tracking {tracked_states} / {len(state_names)} states")
    # Reported marker weights when calling Moco seem to be bugged:
    # always reports non-kinematic states as weight=1.0
    # use verbose flag to look at set weights which should be the correct ones.
    if verbose:
        for i in range(state_weights.getSize()):
            state_weight = state_weights.get(i)
            print(
                f"Marker: {state_weight.getName()}, Weight: {state_weight.getWeight()}"
            )


# Main ------------------------------------------------------------------------
@log_md(md_log_file)
def moco_track_states(
    model_file: Path,
    input_sto_file: Path | None,
    filter_params: dict,
    output_file: Path | None = None,
) -> Path:
    # Handle Paths
    input_sto_file = (
        Path(input_sto_file.name)
        if input_sto_file
        else Path(str(model_file.with_suffix("")) + "_tracked_states.sto")
    )
    output_file = (
        Path(output_file)
        if output_file
        else Path(str(input_sto_file.with_suffix("")) + "_solution.sto")
    )

    # Moco
    track = osim.MocoTrack()
    track.setName(model_file.stem)

    osim.Logger.setLevelString("Info")
    # osim.Logger.setLevelString("Debug")

    # Load model and adapt model
    modelProcessor = osim.ModelProcessor(str(model_file))
    modelProcessor.append(osim.ModOpTendonComplianceDynamicsModeDGF("implicit"))
    modelProcessor.append(osim.ModOpScaleActiveFiberForceCurveWidthDGF(1.5))
    track.setModel(modelProcessor)

    # Load states from .sto
    table_processor = osim.TableProcessor(str(input_sto_file))
    track.setStatesReference(table_processor)
    table = table_processor.process()

    # Set weights
    state_names = table.getColumnLabels()
    state_weights = osim.MocoWeightSet()

    set_state_weights(
        track,
        state_names,
        state_weights,
        filter_params["state_filters"],
        inverse_filter=filter_params["invert_filter"],
        # verbose=True,
    )

    track.set_allow_unused_references(True)
    track.set_track_reference_position_derivatives(True)
    track.set_initial_time(table.getIndependentColumn()[0])
    track.set_final_time(table.getIndependentColumn()[-2])
    track.set_mesh_interval(0.02)
    track.set_apply_tracked_states_to_guess(True)

    study = track.initialize()
    solver = osim.MocoCasADiSolver.safeDownCast(study.updSolver())
    solver.set_optim_max_iterations(3000)
    solver.set_optim_convergence_tolerance(1e-1)
    # solver.set_optim_convergence_tolerance(1e-4)
    solver.set_optim_constraint_tolerance(1e-4)

    solution = study.solve()

    if solution.success() is False:
        output_file = Path(output_file.stem + "_failed.sto")
        solution.unseal()
        solution.write(str(output_file))

        sys.exit(f"-- Tracking failed, writing:\n - {output_file}")
    else:
        output_file = Path(output_file.stem + "_success.sto")
        solution.write(str(output_file))
        full_stride = osim.createPeriodicTrajectory(solution)
        full_stride.write(output_file.stem + "_fullstride.sto")

        print(
            f"-- Tracking succesful, writing:\n - {str(output_file)}\n - {str(output_file.stem + '_fullstride.sto')}"
        )


    # Extract solution muscle fiber data
    try:
        muscle_dynamics_data = study.analyze(
            solution,
            [
                r".*active_fiber_force",
                r".*passive_fiber_force",
                r".*fiber_length",
                r".*fiber_velocity",
                r".*fiber_active_power",
                r".*fiber_passive_power",
                r".*normalized_fiber_length",
                r".*normalized_fiber_velocity",
                r".*activation",
                r".*excitation",
                r".*active_force_length_multiplier",
                r".*normalized_tendon_force",
                r".*tendon_force",
                r".*tendon_length",
                r".*tendon_strain",
                r".*tendon_velocity",
                r".*tendon_power",
            ],
        )

        muscle_dynamics_file = output_file.stem + "_muscle_dynamics.sto"
        osim.STOFileAdapter.write(
            muscle_dynamics_data,
            muscle_dynamics_file,
        )
    except Exception as error:
        print("DYNAMICS ERROR:\n", error)

    return output_file, muscle_dynamics_file


if __name__ == "__main__":
    args = parse_arguments()

    if args.model.parents[0]:
        os.chdir(args.model.parents[0])
        model_file = Path(args.model.name)

    filter_params = {
        "state_filters": args.filter,
        "invert_filter": args.invert_filter,
    }

    moco_track_states(
        Path(args.model),
        Path(args.sto),
        filter_params,
        args.output,
    )
