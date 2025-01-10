import opensim as osim


# Defs ------------------------------------------------------------------------
def extract_muscle_and_bone(model_path):

    model = osim.Model(model_path)
    model.initSystem()

    # Use set to ensure muscles are unique per bone map
    body_muscle_map = {body.getName(): set() for body in model.getBodySet()}

    for muscle in model.getMuscles():
        path_points = muscle.getGeometryPath().getPathPointSet()

        for i in range(path_points.getSize()):
            point = path_points.get(i)

            body_name = point.getBodyName()
            if body_name in body_muscle_map:
                body_muscle_map[body_name].add(muscle.getName())

    return body_muscle_map
