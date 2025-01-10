"""
Parse .osim (.xml) file for jointset and forceset elements.
"""

# Imports ---------------------------------------------------------------------
import argparse
import numpy as np
from pathlib import Path
from lxml import etree


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
        help="Path to input .osim model",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--sto",
        type=str,
        help="Path to solution .sto model",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------


def parse_location(location_str):
    """Convert a location string to a numpy array of floats."""
    return np.array([float(coord) for coord in location_str.split()])


def compute_orientation(vec):
    """Compute the unit vector (orientation) of a vector."""
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec


# Main ------------------------------------------------------------------------
def parse_model_for_states(osim):
    """
    Specific order o
    """
    states = ["time"]
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(osim, parser)
    root = tree.getroot()

    # Jointset values
    joint_set = root.findall("Model/JointSet/objects/")
    joints = [joint for joint in joint_set if joint.tag != "WeldJoint"]
    for joint in joints:
        joint_name = joint.attrib.get("name", "Unnamed Joint")
        coordinates = joint.find("coordinates")
        if coordinates is not None:
            for coordinate in coordinates.findall("Coordinate"):
                coord_name = coordinate.attrib.get("name")
                states.append(f"/jointset/{joint_name}/{coord_name}/value")

    # Jointset speed
    joint_set = root.findall("Model/JointSet/objects/")
    joints = [joint for joint in joint_set if joint.tag != "WeldJoint"]
    for joint in joints:
        joint_name = joint.attrib.get("name", "Unnamed Joint")
        coordinates = joint.find("coordinates")
        if coordinates is not None:
            for coordinate in coordinates.findall("Coordinate"):
                coord_name = coordinate.attrib.get("name")
                states.append(f"/jointset/{joint_name}/{coord_name}/speed")

    # Force activation / normalized tendon force
    force_set = root.findall("Model/ForceSet/objects/")
    forces = [force for force in force_set]
    for force in forces:
        if "DeGroote" in force.tag:
            states.append(f"/forceset/{force.attrib.get('name')}/activation")
            states.append(
                f"/forceset/{force.attrib.get('name')}/normalized_tendon_force"
            )

    # Force
    force_set = root.findall("Model/ForceSet/objects/")
    forces = [force for force in force_set]
    for force in forces:
        if "DeGroote" in force.tag:
            states.append(f"/forceset/{force.attrib.get('name')}")

    # Jointset accel
    joint_set = root.findall("Model/JointSet/objects/")
    joints = [joint for joint in joint_set if joint.tag != "WeldJoint"]
    for joint in joints:
        joint_name = joint.attrib.get("name", "Unnamed Joint")
        coordinates = joint.find("coordinates")
        if coordinates is not None:
            for coordinate in coordinates.findall("Coordinate"):
                coord_name = coordinate.attrib.get("name")
                states.append(f"/jointset/{joint_name}/{coord_name}/accel")

    # Force implicitderiv_normalized_tendon_force
    force_set = root.findall("Model/ForceSet/objects/")
    forces = [force for force in force_set]
    for force in forces:
        if "DeGroote" in force.tag:
            states.append(
                f"/forceset/{force.attrib.get('name')}/implicitderiv_normalized_tendon_force"
            )

    return states


def parse_model_for_joints(osim):
    joint_states = {}
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(osim, parser)
    root = tree.getroot()

    joint_set = root.findall("Model/JointSet/objects/")
    # joints = [joint for joint in joint_set if joint.tag != "WeldJoint"]
    joints = [joint for joint in joint_set]
    for joint in joints:
        joint_name = joint.attrib.get("name")
        if not joint_name:
            continue

        joint_states[joint_name] = []
        coordinates = joint.find("coordinates")
        if coordinates is not None:
            for coordinate in coordinates.findall("Coordinate"):
                coord_name = coordinate.attrib.get("name")
                joint_states[joint_name].append(coord_name)

    return joint_states


def parse_model_for_force_vector(osim, sto):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(osim, parser)

    muscles = tree.xpath("//DeGrooteFregly2016Muscle")

    # Data structure to store results
    force_vector_data = {}

    for muscle in muscles:
        muscle_name = muscle.get("name")
        path_points = muscle.xpath(".//PathPoint")

        if len(path_points) < 2:
            continue

        second_to_last = path_points[-2]
        last = path_points[-1]

        second_to_last_location = parse_location(second_to_last.findtext("location"))
        last_location = parse_location(last.findtext("location"))

        vector = last_location - second_to_last_location
        orientation = compute_orientation(vector)

        force_vector_data[muscle_name] = {
            "second_to_last_pathpoint_name": second_to_last.get("name"),
            "second_to_last_location": second_to_last_location.tolist(),
            "origin_pathpoint_name": last.get("name"),
            "origin": last_location.tolist(),
            "vector_orientation": orientation.tolist(),
        }

    return force_vector_data


if __name__ == "__main__":
    args = parse_arguments()

    # states = parse_model_for_states(Path(args.input))
    # parse_model_for_force_vector(args.input, args.sto)
    parse_model_for_joints(args.input)

    # [print(state) for state in states]
