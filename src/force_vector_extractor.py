"""Extract muscle force vector and orientation"""

# Imports ---------------------------------------------------------------------
import os
import math
import numpy as np
import pandas as pd
import opensim as osim
from pathlib import Path


# Defs ------------------------------------------------------------------------
def extract_force_vectors(osim_path, sto_path, output_path):
    # Load input
    model = osim.Model(osim_path)
    sto_data = osim.TimeSeriesTable(sto_path)

    # Initiate output
    force_origins = {}
    force_directions = {"time": []}
    previous = {}
    current = {}

    muscles = model.getMuscles()
    for muscle_name in [muscles.get(i).getName() for i in range(muscles.getSize())]:
        force_origins[muscle_name] = []
        force_directions[muscle_name] = []
        previous[muscle_name] = []
        current[muscle_name] = []

    # Initiate model state
    state = model.initSystem()

    # Build a coordinate map to track and update model states through time
    model_coordinates = {coord.getName(): coord for coord in model.getCoordinateSet()}
    sto_to_coord_map = {}
    for label in sto_data.getColumnLabels():
        if "/value" in label:
            coord_name = label.split("/")[-2]
            if coord_name in model_coordinates:
                sto_to_coord_map[label] = coord_name

    # Iterate through time steps in the .sto file
    for time_index in range(sto_data.getNumRows()):
        time = sto_data.getIndependentColumn()[time_index]
        force_directions["time"].append(time)

        # Update model states
        for sto_label, coord_name in sto_to_coord_map.items():
            value = sto_data.getDependentColumn(sto_label)[time_index]
            coord = model.updCoordinateSet().get(coord_name)
            coord.setValue(state, value)
        model.realizeDynamics(state)

        # Extract muscle path points in current state
        for i in range(muscles.getSize()):
            muscle = muscles.get(i)
            geom_path = muscle.getGeometryPath()

            point_force_directions = osim.ArrayPointForceDirection()
            geom_path.getPointForceDirections(state, point_force_directions)
            geom_path.updateGeometry(state)

            # Last point = point of muscle insertion
            insertion_index = point_force_directions.getSize() - 1

            pfd = point_force_directions.get(insertion_index)

            print(f"{muscle.getName()}: {pfd.direction()}")

            insertion_in_ground = [
                pfd.frame().findStationLocationInGround(state, pfd.point())[0],
                pfd.frame().findStationLocationInGround(state, pfd.point())[1],
                pfd.frame().findStationLocationInGround(state, pfd.point())[2],
            ]
            # #     pfd.frame().findStationLocationInAnotherFrame(state, pfd.point(), pfd.frame())[0],
            # #     pfd.frame().findStationLocationInAnotherFrame(state, pfd.point(), pfd.frame())[1],
            # #     pfd.frame().findStationLocationInAnotherFrame(state, pfd.point(), pfd.frame())[2],
            # # ]
            # print(f"Insertion: {insertion_in_ground}")
            #
            pfd2 = point_force_directions.get(insertion_index - 1)
            print(f"{muscle.getName()}: first {pfd.point()} second {pfd2.point()}")
            previous_in_ground = [
                pfd2.frame().findStationLocationInGround(state, pfd2.point())[0],
                pfd2.frame().findStationLocationInGround(state, pfd2.point())[1],
                pfd2.frame().findStationLocationInGround(state, pfd2.point())[2],
            ]
            #     pfd2.frame().findStationLocationInAnotherFrame(state, pfd2.point(), pfd.frame())[0],
            #     pfd2.frame().findStationLocationInAnotherFrame(state, pfd2.point(), pfd.frame())[1],
            #     pfd2.frame().findStationLocationInAnotherFrame(state, pfd2.point(), pfd.frame())[2],
            # ]

            insertion_vector = [
                v1 - v2 for v1, v2 in zip(previous_in_ground, insertion_in_ground)
            ]
            normalized_vector = insertion_vector / np.linalg.norm(insertion_vector)
            print(f"Normalized: {normalized_vector}")


            transform = model.getGround().findTransformBetween(state, pfd.frame())
            normalized_vector = osim.Vec3(normalized_vector)
            rotated_vector = transform.R().multiply(normalized_vector)

            # prev_in_insertion = pfd2.frame().findStationLocationInAnotherFrame(
            #     state, pfd2.point(), pfd.frame()
            # )
            # print(prev_in_insertion)

            # changed_vector = pfd.frame().expressVectorInAnotherFrame(
            #     state,
            #     pfd.direction(),
            #     pfd.frame(),
            # )
            # print(normalized_vector, changed_vector)

            force_directions[muscle.getName()].append(
                [
                    math.degrees(rotated_vector[0]),
                    math.degrees(rotated_vector[1]),
                    math.degrees(rotated_vector[2]),
                ]
                # [
                #     math.degrees(normalized_vector[0]),
                #     math.degrees(normalized_vector[1]),
                #     math.degrees(normalized_vector[2]),
                # ]
                # [
                #     math.degrees(changed_vector[0]),
                #     math.degrees(changed_vector[1]),
                #     math.degrees(changed_vector[2]),
                # ]
                # [
                #     math.degrees(pfd.direction()[0]),
                #     math.degrees(pfd.direction()[1]),
                #     math.degrees(pfd.direction()[2]),
                # ]
            )

            force_origins[muscle.getName()].append(
                [
                    pfd.point()[0],
                    pfd.point()[1],
                    pfd.point()[2],
                ]
            )
            # force_origins[muscle.getName()].append(
            #         previous_in_ground
            # )

            # current[muscle.getName()].append(
            #     [
            #         pfd.point()[0],
            #         pfd.point()[1],
            #         pfd.point()[2],
            #     ]
            # )
            # # current[muscle.getName()].append(
            # #     insertion_in_ground
            # # )
            # previous[muscle.getName()].append(
            #     previous_in_ground
            # )

    # previous_path = os.path.join(
    #     output_path, f"{Path(sto_path).stem}_previous.json"
    # )
    # current_path = os.path.join(
    #     output_path, f"{Path(sto_path).stem}_current.json"
    # )
    # pd.DataFrame(previous).to_json(
    #     previous_path, orient="records", lines=True
    # )
    # pd.DataFrame(current).to_json(
    #     current_path, orient="records", lines=True
    # )

    # Save to json
    force_origin_paths = os.path.join(
        output_path, f"{Path(sto_path).stem}_muscle_origins.json"
    )
    force_vector_paths = os.path.join(
        output_path, f"{Path(sto_path).stem}_muscle_vectors.json"
    )

    pd.DataFrame(force_origins).to_json(
        force_origin_paths, orient="records", lines=True
    )
    pd.DataFrame(force_directions).to_json(
        force_vector_paths, orient="records", lines=True
    )

    return force_origin_paths, force_vector_paths
