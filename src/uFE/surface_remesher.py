"""
Remesh an existing surface mesh that may or may not be scuffed.
"""
# Imports ---------------------------------------------------------------------
import os
import numpy as np
import pyvista as pv
import open3d as o3d
import argparse

from utils.formatting import print_status, print_section, timer


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
        help="Input path to directory containing stack of medical image tiff files",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output filename (.ply)",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
@timer
def reconstruct_surface_mesh_from_points(input_file):
    print("-- Reconstructing surface mesh...")
    points = pv.read(input_file).points

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    pcd.normals = o3d.utility.Vector3dVector(np.zeros((len(pcd.points), 3)))

    print(" - Re-orienting normals...")
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=0.1,
            max_nn=5,
        )
    )
    pcd.orient_normals_consistent_tangent_plane(10)

    print(" - Reconstructing surface...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd,
        depth=8,
    )

    mesh = mesh_cleanup(mesh, densities)

    vertices = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.triangles)

    faces_pv = (
        np.hstack([np.full((faces.shape[0], 1), 3), faces]).astype(np.int32).flatten()
    )

    polydata = pv.PolyData(vertices, faces_pv)
    polydata.compute_normals(inplace=True)

    polydata.plot_normals(mag=0.003, flip=True, show_edges=True, color="red")
    # signed_distances = polydata.point_data["implicit_distance"]
    offset_distance = 0.001
    offset_points = polydata.points + offset_distance * polydata.point_data["Normals"]
    offset_points = pv.PolyData(offset_points)

    offset_points.compute_implicit_distance(polydata, inplace=True)

    for i, orient in enumerate(offset_points.point_data["implicit_distance"]):
        if orient > float(0):
            print(i, orient)
            polydata.point_data["Normals"][i] = polydata.point_data["Normals"][i] * -1

    pl = pv.Plotter()
    # pl.add_mesh(offset_points, color="red")
    pl.add_mesh(polydata.points, color="blue")
    pl.add_mesh(
        offset_points,
        scalars="implicit_distance",
        cmap="coolwarm",
        # clim=[-1, 1],
    )
    pl.add_mesh(polydata, show_edges=True, color="white")
    pl.show()

    polydata.plot_normals(
        mag=0.0005,
        flip=False,
        show_edges=True,
        color="red",
        scalars=None,
    )

    return mesh, densities


@timer
def mesh_cleanup(mesh, densities, smooth_iterations=100):
    print_section()
    print("-- Cleaning mesh...")
    # Clear up mesh based on vertex density
    mesh.remove_vertices_by_mask(densities < np.quantile(densities, 0.01))

    # Cleanup mesh
    mesh.remove_duplicated_vertices()
    mesh.remove_duplicated_triangles()
    mesh.remove_non_manifold_edges()
    mesh.remove_unreferenced_vertices()

    mesh.filter_smooth_taubin(number_of_iterations=smooth_iterations)

    return mesh


@timer
def write_output(
    output_file,
    mesh,
):
    print_section()

    print(f"-- Writing file:\n - {os.path.basename(output_file)}")

    o3d.io.write_triangle_mesh(
        str(output_file),
        mesh,
        write_vertex_normals=True,
    )

    return output_file


# Main ------------------------------------------------------------------------
def remesh_surface(
    input_file,
    output_file,
    visuals=False,
):
    print_section()
    print(f"-- Surface remeshing initiated - loading file:\n - {str(input_file)}")

    mesh, densities = reconstruct_surface_mesh_from_points(input_file)

    mesh = mesh_cleanup(mesh, densities)

    output_file = write_output(output_file, mesh)

    if visuals:
        pv.read(output_file)

        mesh = pv.read(output_file)
        mesh.plot_normals(mag=0.001, flip=True, show_edges=True, color="red")

        pl = pv.Plotter()
        pl.add_mesh(pv.read(output_file), color="white", scalars=None)
        pl.add_mesh(pv.read(output_file).points, color="blue", scalars=None)
        # pl.add_mesh(pv.read(input_file).points, color="red", scalars=None)
        pl.show()


if __name__ == "__main__":
    args = parse_arguments()

    remesh_surface(
        args.input,
        args.output,
        visuals=args.visuals,
    )
