"""Extract muscle force vector and orientation"""

# Imports ---------------------------------------------------------------------
import os
import math
import numpy as np
import pandas as pd
import opensim as osim
from pathlib import Path


# Defs ------------------------------------------------------------------------
def extract_force_vectors(osim_path, sto_path, boi, output_path):
    # Load input
    model = osim.Model(osim_path)
    sto_data = osim.TimeSeriesTable(sto_path)

    # Initiate output
    force_origins = {}
    force_directions = {"time": []}

    muscles = model.getMuscles()

    for muscle in muscles:
        path_points = muscle.getGeometryPath().getPathPointSet()
        for i in range(path_points.getSize()):
            point = path_points.get(i)
            if point.getBodyName() in boi:
                if i == 0 or i == path_points.getSize() - 1:
                    force_origins[muscle.getName()] = []
                    force_directions[muscle.getName()] = []
                else:
                    continue

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
        for muscle in muscles:
            point_force_directions = osim.ArrayPointForceDirection()
            geom_path = muscle.getGeometryPath()
            geom_path.updateGeometry(state)
            geom_path.getPointForceDirections(state, point_force_directions)

            path_points = geom_path.getPathPointSet()
            for i in range(path_points.getSize()):
                point = path_points.get(i)
                if point.getBodyName() in boi:
                    if i == 0:
                        insertion_index = 0
                        other_index = 1
                    elif i == path_points.getSize() - 1:
                        insertion_index = point_force_directions.getSize() - 1
                        other_index = insertion_index - 1
                    else:
                        continue

                    pfd = point_force_directions.get(insertion_index)
                    pfd2 = point_force_directions.get(other_index)

                    insertion_in_ground = [
                        pfd.frame().findStationLocationInGround(state, pfd.point())[0],
                        pfd.frame().findStationLocationInGround(state, pfd.point())[1],
                        pfd.frame().findStationLocationInGround(state, pfd.point())[2],
                    ]

                    previous_in_ground = [
                        pfd2.frame().findStationLocationInGround(state, pfd2.point())[
                            0
                        ],
                        pfd2.frame().findStationLocationInGround(state, pfd2.point())[
                            1
                        ],
                        pfd2.frame().findStationLocationInGround(state, pfd2.point())[
                            2
                        ],
                    ]

                    insertion_vector = [
                        v1 - v2
                        for v1, v2 in zip(previous_in_ground, insertion_in_ground)
                    ]
                    normalized_vector = insertion_vector / np.linalg.norm(
                        insertion_vector
                    )
                    normalized_vector = osim.Vec3(normalized_vector)
                    transform = model.getGround().findTransformBetween(
                        state, pfd.frame()
                    )
                    rotated_vector = transform.R().multiply(normalized_vector)

                    force_origins[muscle.getName()].append(
                        [
                            pfd.point()[0],
                            pfd.point()[1],
                            pfd.point()[2],
                        ]
                    )
                    force_directions[muscle.getName()].append(
                        [
                            math.degrees(rotated_vector[0]),
                            math.degrees(rotated_vector[1]),
                            math.degrees(rotated_vector[2]),
                        ]
                    )

    force_origin_paths = os.path.join(
        output_path, f"{Path(sto_path).stem}_{boi}_muscle_origins.json"
    )
    force_vector_paths = os.path.join(
        output_path, f"{Path(sto_path).stem}_{boi}_muscle_vectors.json"
    )

    pd.DataFrame(force_origins).to_json(
        force_origin_paths, orient="records", lines=True
    )
    pd.DataFrame(force_directions).to_json(
        force_vector_paths, orient="records", lines=True
    )

    return force_origin_paths, force_vector_paths


def extract_model_bones(model_path):
    model = osim.Model(model_path)
    model.initSystem()

    bodies_with_muscles = set()

    for i in range(model.getMuscles().getSize()):
        muscle = model.getMuscles().get(i)
        origin_body = muscle.getGeometryPath().getPathPointSet().get(0).getBodyName()
        insertion_body = (
            muscle.getGeometryPath()
            .getPathPointSet()
            .get(muscle.getGeometryPath().getPathPointSet().getSize() - 1)
            .getBodyName()
        )

        bodies_with_muscles.add(origin_body)
        bodies_with_muscles.add(insertion_body)

    bodies_with_muscles = list(bodies_with_muscles)

    return bodies_with_muscles
