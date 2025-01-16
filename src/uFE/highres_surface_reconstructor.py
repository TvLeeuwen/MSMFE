"""
Reconstruct surface mesh from medical image data stack by calling `reconstruct_surface()`

:param `input_data`: Path/to/input/data/stack/directory(.tifs)
:param `output_file`: Path/to/output_file(.ply): default uses `input_data`
:(optional) param `start_slice`: First slice from the stack to be considered. Allows for cropping.
:(optional) param `end_slice`: Last slice to be included in the stack. Allows from cropping.
:(optional) param `thresh_lower`: Lower threshold value, everything above is considered part of the geometry.
:(optional) param `thresh_upper`: Upper threshold value, everything below is considered part of the geometry.
:(optional) param `qa`: Toggle automatic quality assurance. Repairs surface mesh for further use.
:(optional) param `visuals`: Toggle visual feedback.
:output surface mesh .ply file of name `output_file`
"""

# Imports ---------------------------------------------------------------------
import os
import sys
from sys import getsizeof
import argparse
from pathlib import Path
import numpy as np
from numpy.typing import NDArray
import tifffile
import pyvista as pv
import cv2
import cc3d
import open3d as o3d
from scipy.ndimage import binary_erosion, binary_dilation, sobel
from skimage import feature, filters, io as skio
from matplotlib import pyplot as plt


sys.path.insert(0, str(Path(__file__).parents[1]))
from utils.formatting import print_status, print_section, timer
from utils.handle_args import handle_args_suffix
from utils.visualisation import visualize_stack
from uFE.qa_highres_surface import assure_surface_mesh_quality

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
        "-s",
        "--start",
        type=int,
        help=f"Start slice of the stack to be considered, default=0 (first slice of the stack)",
        default=0,
    )
    parser.add_argument(
        "-l",
        "--last",
        type=int,
        help=f"Last slice from the datastack to be included, default=-1 (last slice of the stack)",
        default=-1,
    )
    parser.add_argument(
        "-tl",
        "--thresh_lower",
        type=int,
        help=f"Reconstruction threshold lower value, must be > 0 but < -tu and 255, default=80",
        default=80,
    )
    parser.add_argument(
        "-tu",
        "--thresh_upper",
        type=int,
        help=f"Reconstruction threshold upper value, must be > 0 and -tl but < 255, default=255",
        default=255,
    )
    parser.add_argument(
        "-f",
        "--fill",
        action="store_true",
        help="Fill geometry before extracting the outline - no internal geometry",
    )
    parser.add_argument(
        "-nqa",
        "--noquality",
        action="store_false",
        help="Deactivate automatic quality assurance",
    )
    parser.add_argument(
        "-v",
        "--visuals",
        action="store_true",
        help="Activate visual feedback",
    )
    return parser.parse_args()


# Defs ------------------------------------------------------------------------
def handle_args_input_params(start_slice: int, end_slice: int, thresh_lower: int, thresh_upper: int):
        if end_slice == -1:
            pass
        elif start_slice < 0:
            sys.exit(f"Start slice ({start_slice}) and end slices ({end_slice}) must be positive integers.")
        elif start_slice > end_slice:
            sys.exit(f"Start slice ({start_slice})  must come before end slice ({end_slice}).")

        if thresh_lower < 0:
            sys.exit(f"Lower threshold ({thresh_lower}) needs to exceed 0.")
        elif thresh_lower > thresh_upper:
            sys.exit(f"Lower threshold ({thresh_lower}) can not exceed upper threshold ({thresh_upper}).")
        elif thresh_upper > 255:
            sys.exit(f"Upper threshold ({thresh_upper}) is bound to a maximum of 255.")


@timer
def load_img(input, start=0, end=-1):

    format = "tiff" if not input.suffix else input.suffix

    img = None
    match format:
        case ".mhd":
            img = skio.imread(input, plugin='simpleitk')
            img = img[start:end]

        case "tiff":
            input_slices = [
                os.path.join(input, file)
                for file in os.listdir(input)
            ]
            img = tifffile.imread(input_slices[start:end])

    print_status(
        " - Loading complete, image size:",
        f"{img.shape[0]}, {img.shape[1]}, {img.shape[2]}",
    )

    return img


@timer
def trim_zeros(arr, margin=0, quiet=False, visual=True):
    """
    Trim the leading and trailing zeros from a N-D array.
    @params
    :param arr: numpy array
    :param margin: how many zeros to leave as a margin
    @returns: trimmed array, slice object
    By Alex - https://stackoverflow.com/questions/55917328/numpy-trim-zeros-in-2d-or-3d
    """
    s = []
    for dim in range(arr.ndim):
        start = 0
        end = -1
        slice_ = [slice(None)] * arr.ndim
        go = True
        while go:
            slice_[dim] = start
            go = not np.any(arr[tuple(slice_)])
            start += 1
        start = max(start - 1 - margin, 0)
        go = True
        while go:
            slice_[dim] = end
            go = not np.any(arr[tuple(slice_)])
            end -= 1
        end = arr.shape[dim] + min(-1, end + 1 + margin) + 1
        s.append(slice(start, end))

    if np.amax(arr[tuple(s)]) == 0:
        sys.exit("-- Empty image loaded, exiting module...")

    if not quiet:
        print_status(
            " - Image trimmed, new size:",
            f"{arr[tuple(s)].shape[0]}, {arr[tuple(s)].shape[1]}, {arr[tuple(s)].shape[2]}",
        )

    if visual:
        visualize_stack(arr[tuple(s)])

    return arr[tuple(s)]


@timer
def threshold_image_stack(img: NDArray, t_lower: int, t_upper: int, binary: bool=False, visual: bool=True,) -> NDArray:
    """
    Thresholds the image stack based on a lower and upper threshold value

    :param img: 3D image stack.
    :param t_lower: Lower threshold value. Values below are set to zero.
    :param t_upper: Upper threshold value. Values above are set to zero.
    :param binary: Set threshold type to either binary or truncated original image.
    :param visual: Toggle visual feedback.
    """

    if binary:
        thresh_type = cv2.THRESH_BINARY
    else:
        thresh_type = cv2.THRESH_TOZERO
    # TODO: Add viewer of one slice with slider giving feedback to the user what thresh to pick
    print("-- Thresholding image...")
    for i, im in enumerate(img):
        _, thresh = cv2.threshold(im, t_lower, t_upper, thresh_type)
        img[i] = thresh

    if visual:
        visualize_stack(img)

    return img


def generate_outline(img, method="binary_erosion", fill=True, visual=True,):
    """
    Generate outline for Poisson's surface reconstruction.

    :param img: 3D image stack
    :param method: method for generating the outline, options below:
    :: `"binary_erosion"`: binary erosian mask
    :: `"canny_edge"`: Canny edge detection
    :: `"canny_edge_cv"`: Canny edge detection - OpenCV implementation
    :: `"sobels_edge"`: Sobels edge detection
    :: `"roberts_edge"`: Roberts edge detection
    :param fill: Toggle to include/exclude internal geometry.
    :: `True` will fill the geometry to generate a surface outline only.
    :: `False` will include the internal geometry.
    :param visual: Toggle visual feedback
    """

    print(f"-- Detecting edges using '{method}' and fill={fill}")

    if fill:
        img = fill_geometry(img, visual=False, iterations=10,)
        if visual:
            visualize_stack(img)

    print(" - Edge detection...")
    match method:
        case "binary_erosion":
            img = binary_erosian_image_stack(img, visual=False)
        case "canny_edge":
            img = canny_edge_image_stack(
                img,
                low_threshold=0.1,
                high_threshold=0.3,
                sigma=1,
                visual=False,
            )
        case "canny_edge_cv":
            img = canny_edge_cv2(img)
        case "sobels_edge":
            img = sobel_edge_image_stack(img, visual=False)

        case "roberts_edge":
            img = roberts_edge_image_stack(img, visual=False)
        case _:
            print(f"-- WARNING: {method} is not an available method!")
            sys.exit("-- Exiting script")

    if visual:
        visualize_stack(img)

    return img


@timer
def fill_geometry(binary_stack, visual=True, iterations=5):
    """Fills the internal morphology using a mask of the negative space around the geometry.
    Requires the geometry to be non porous - which is achieved using dilation/erosion.
    Minimize dilation/erosion iterations to retain maximum surface detail.
    @params:
        binary_stack: image stack containing the geometry to be filled.
        iterations: number of dilation/erosion iterations, affects gap fill but also loss of detail.
    @returns:
        result_stack of binary_stack dimensions containing a filled geometry.
    """

    print(" - Filling geometry...")
    # Dilate to close holes in exterior
    binary_stack = binary_dilation(binary_stack, iterations=iterations)
    binary_stack = binary_erosion(binary_stack, iterations=iterations)

    filled_stack = binary_stack.copy()
    filled_stack[:] = 1
    result_stack = filled_stack.copy()
    filled_stack[binary_stack] = 0

    # Isolate k largest structures
    stack_geometries, _ = cc3d.largest_k(
        filled_stack,
        k=1,
        connectivity=26,
        delta=0,
        return_N=True,
    )
    for _, geom in cc3d.each(stack_geometries, binary=False, in_place=True):
        result_stack = result_stack - geom

    if visual:
        visualize_stack(result_stack)

    return result_stack


@timer
def binary_erosian_image_stack(binary_stack, visual=True):
    """Image stack surface voxel extraction by means of binary erosion"""
    eroded_stack = binary_erosion(binary_stack, iterations=1)
    result_stack = binary_stack.copy()
    result_stack[eroded_stack] = 0

    if visual:
        visualize_stack(result_stack)

    return result_stack


@timer
def canny_edge_image_stack(
    img,
    low_threshold=0.1,
    high_threshold=0.3,
    sigma=1,
    visual=True,
):
    canny_edge_img = np.array(
        [
            feature.canny(
                slice,
                low_threshold=low_threshold,
                high_threshold=high_threshold,
                sigma=sigma,
            )
            for slice in img
        ]
    )

    if visual:
        visualize_stack(canny_edge_img)

    return canny_edge_img


@timer
def canny_edge_cv2(img):

    if img.dtype != np.uint8:
        img = img.astype(np.uint8)

    canny_edge_img = np.array(
        [
            cv2.Canny(slice*255, 100, 200)
            for slice in img
        ]
    )

    return canny_edge_img


@timer
def sobel_edge_image_stack(img, visual=True,):

    img = img*255

    sobel_x = sobel(img, axis=0)
    sobel_y = sobel(img, axis=1)
    sobel_z = sobel(img, axis=2)

    # Compute the gradient magnitude
    img = np.sqrt(sobel_x**2 + sobel_y**2 + sobel_z**2)

    if visual:
        visualize_stack(img)

    return img


@timer
def roberts_edge_image_stack(img, visual=True,):

    img = np.array([filters.sobel(slice) for slice in img])

    if visual:
        visualize_stack(img)

    return img


@timer
def reconstruct_surface_mesh_from_image(image, visual=True):

    print("-- Reconstructing surface mesh...")
    points = np.vstack((np.nonzero(image))).T

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    if visual:
        o3d.visualization.draw_geometries([pcd])

    print(" - Re-orienting normals...")
    pcd.estimate_normals()
    pcd.orient_normals_consistent_tangent_plane(30)

    print(" - Reconstructing surface...")
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=10
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

    mesh.compute_vertex_normals()

    return(mesh)

@timer
def mesh_quality_assessment(mesh):
    print("-- Quality assessment in progress...")

    edge_manifold = mesh.is_edge_manifold(allow_boundary_edges=True)
    print_status(" - edge manifold:", f"{edge_manifold}")
    edge_manifold_boundary = mesh.is_edge_manifold(allow_boundary_edges=False)
    print_status(" - edge manifold boundary:", f"{edge_manifold_boundary}")
    vertex_manifold = mesh.is_vertex_manifold()
    print_status(" - vertex manifold:", f"{vertex_manifold}")

    if edge_manifold or edge_manifold_boundary or vertex_manifold is False:
        print(" - Warning: QA failed: run QA module before mesh adaptation.")

@timer
def write_output(output_file: Path, mesh,):

    print_section()

    output_file = handle_args_suffix(output_file, suffix=".ply")

    print(f"-- Writing file:\n - {output_file.name}")

    o3d.io.write_triangle_mesh(str(output_file), mesh, write_vertex_normals=True,)

    return output_file

# Main -----------------------------------------------------------------------
@timer
def reconstruct_surface(
    input_data: Path,
    output_file: Path,
    start_slice: int = 0,
    end_slice: int = -1,
    thresh_lower: int = 80,
    thresh_upper: int = 255,
    fill: bool = True,
    qa: bool = True,
    visuals: bool = False,
):
    """
    Reconstruct surface mesh from medical image data stack.

    :param `input_data`: Path/to/input/data/stack/directory(.tifs).
    :param `output_file`: Path/to/output_file(.ply).
    :(optional) param `start_slice`: First slice from the stack to be considered. Allows for cropping.
    :(optional) param `end_slice`: Last slice to be included in the stack. Allows from cropping.
    :(optional) param `thresh_lower`: Lower threshold value, everything above is considered part of the geometry.
    :(optional) param `thresh_upper`: Upper threshold value, everything below is considered part of the geometry.
    :(optional) param `qa`: Toggle automatic quality assurance. Calls `assure_surface_mesh_quality()`.
    :(optional) param `visuals`: Toggle visual feedback.
    :output surface mesh .ply file of name `output_file`
    """

    handle_args_input_params(start_slice, end_slice, thresh_lower, thresh_upper)

    print_section()
    print(f"-- Surface reconstruction initiated - loading image:\n - {str(input_data)}",)

    image_sequence = load_img(input_data, start_slice, end_slice)

    image_sequence = threshold_image_stack(
        image_sequence, thresh_lower, thresh_upper, binary=True, visual=visuals,
    )

    image_sequence = trim_zeros(image_sequence, visual=visuals,)

    # Geometry isolation -----------------------------------------------------
    # TODO: allow the user to cycle through geometries and select the bone of interest

    # replace for loop/list comp with selected label in list

    # Bone selector / isolator #
    # https://pypi.org/project/connected-components-3d/
    # https://github.com/seung-lab/connected-components-3d
    # Despeckle #
    # cc3d below has a despeckle fuction named dust

    # Isolate k largest structures #
    image_sequence, n_labels = cc3d.largest_k(
        image_sequence,
        k=1,
        connectivity=26,
        delta=0,
        return_N=True,
    )

    for label, image in cc3d.each(image_sequence, binary=False, in_place=True):

        print_section()
        print_status(
            f"-- Reconstructing bone: {label}, size:",
            f"{image.shape[0]}, {image.shape[1]}, {image.shape[2]}",
        )

        image = trim_zeros(np.array(image), margin=10, visual=visuals)
        grid = pv.wrap(image)
        contour = grid.contour(isosurfaces=[1], progress_bar=True)
        smooth_contour = contour.smooth(n_iter=20, relaxation_factor=0.1)

        plotter = pv.Plotter()
        plotter.add_mesh(smooth_contour, color="white")
        plotter.show()


        sys.exit()

        # image = generate_outline(image, method="binary_erosion", fill=fill, visual=visuals)
        image = generate_outline(image, method="sobels_edge", fill=fill, visual=visuals)
        # image = image1*image2

    mesh, densities = reconstruct_surface_mesh_from_image(image, visual=visuals)

    mesh = mesh_cleanup(mesh, densities)

    mesh_quality_assessment(mesh)

    if visuals:
        mesh.paint_uniform_color([1, 1, 1])
        o3d.visualization.draw_geometries_with_editing([mesh])

    output_file = write_output(output_file, mesh)

    if qa:
        assure_surface_mesh_quality(output_file)

    print("-- Surface reconstruction complete, total time elapsed:")


if __name__ == "__main__":
    args = parse_arguments()

    reconstruct_surface(
        Path(args.input),
        Path(args.output),
        start_slice=args.start,
        end_slice=args.last,
        thresh_lower=args.thresh_lower,
        thresh_upper=args.thresh_upper,
        fill=args.fill,
        qa=args.noquality,
        visuals=args.visuals,
    )
