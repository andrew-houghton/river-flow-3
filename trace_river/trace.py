from pyproj import Proj
from pathlib import Path
import rasterio as rio
from matplotlib import pyplot as plt
from algorithms import flood_low_points, add_tile_to_graph
from pprint import pprint
from graph_verify import check_equal_height_nodes, check_flooded_nodes
import numpy as np


proj_string = "+proj=utm +zone=55 +south +datum=WGS84 +units=m +no_defs"
proj = Proj(proj_string)
heights_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "heights.tif")
)
colour_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour.tif")
)
TIF_MAX_DIMENSIONS = (30978, 30978)
GRID = 100
assert heights_tif_path.exists()


def lat_lon_to_row_col(lat, lon):
    # Note: rounds to nearest point
    x, y = proj(lon, lat)
    x = x / 10 - 30000
    y = 550000 - y / 10
    return int(y), int(x)


def get_raster(segment):
    window = rio.windows.Window(
        col_off=segment[1] * GRID,
        row_off=segment[0] * GRID,
        width=GRID,
        height=GRID,
    )
    with rio.open(heights_tif_path) as heights:
        return heights.read(1, window=window)


def trace_and_expand_existing_graph(start_point, end_point):
    start_rowcol = lat_lon_to_row_col(*start_point)
    end_rowcol = lat_lon_to_row_col(*end_point)

    starting_segment = (start_rowcol[0] // GRID, start_rowcol[1] // GRID)
    active_segments = [starting_segment]
    heights = np.zeros(TIF_MAX_DIMENSIONS)
    heights[
        starting_segment[0] * GRID : starting_segment[0] * GRID + GRID,
        starting_segment[1] * GRID : starting_segment[1] * GRID + GRID,
    ] = get_raster(starting_segment)

    graph = add_tile_to_graph(heights, GRID, starting_segment, active_segments)
    graph = flood_added_tile(graph, heights)

    key_lookup = {k: key for key in graph.keys() for k in key}
    path = [key_lookup[start_window_rowcol]]

    closest_finish_point = None
    finish_point_threshold = 10

    for i in range(10000):
        current_point = path[-1]
        next_points = graph[current_point]
        if len(next_points) == 0:
            required_tile = detect_edge_touch(
                current_point,
                active_segments,
            )
            active_segments.append(required_tile)
            segment_raster = get_raster(required_tile)
            heights[
                required_tile[0] * GRID : required_tile[0] * GRID + GRID,
                required_tile[1] * GRID : required_tile[1] * GRID + GRID,
            ] = raster
            graph = add_tile_to_graph(graph, required_tile, heights)
            graph = flood_added_tile(graph, required_tile, heights)

        selected_point = min(
            next_points, key=lambda node_key: height_raster[node_key[0]]
        )
        distance = distance_closest_point(end_rowcol, selected_point)
        if closest_finish_point is not None:
            if distance > distance_closest_point(end_rowcol, closest_finish_point):
                # We're getting further away so just finish without the last point
                return path
            else:
                closest_finish_point = selected_point
        elif distance < finish_point_threshold:
            closest_finish_point = selected_point

        path.append(selected_point)

    print("Algorithm passed iteration limit")
    return path


def apply_window_to_rowcol(window, rowcol):
    # Convert co-ordinates to be relative to a window
    return rowcol[0] - window.row_off, rowcol[1] - window.col_off


def find_centerpoint(node_key):
    x = sum(i[0] for i in node_key) / len(node_key)
    y = sum(i[1] for i in node_key) / len(node_key)
    return x, y


def detect_edge_touch(shape, node, size_factors):
    enlarge = [False, False, False, False]
    for point in node:
        if point[0] == 0:
            enlarge[0] = True
        if point[1] == 0:
            enlarge[2] = True
        if point[0] >= shape[0] - 1:
            enlarge[1] = True
        if point[1] >= shape[1] - 1:
            enlarge[3] = True
    assert any(
        enlarge
    ), "This condition should only happen when the path reaches an edge"
    return [sf * 1.5 if e else sf for e, sf in zip(enlarge, size_factors)]


def show_plot(heights, start, end, dest, path):
    plt.imshow(heights)
    for point in path:
        point = find_centerpoint(point)
        plt.plot(point[1], point[0], "go")
    plt.plot(start[1], start[0], "ro")
    plt.plot(end[1], end[0], "bo")
    plt.plot(dest[1], dest[0], "yo")
    plt.show()


def distance_closest_point(end, node_key):
    node = min(node_key, key=lambda x: abs(end[0] - x[0]) + abs(end[1] - x[1]))
    return node, abs(end[0] - node[0]) + abs(end[1] - node[1])


# TODO figure out a neater version of the algorithm which just expands the area
# When stitching on a new segment to the graph;
# equal height nodes should be merged
# flooding should occur for any low points which remain in the graph (pretty sure this is satisfactory)
# Things to POC:
# - Does stitching maintain the desired properties of the graph
# To test we should be able to assert that the from 2 joined sections is the same as
# the original graph made from doing both sections at once
# - Can we find the edges easily?
# - Can we make a memory efficient storage for heights and display this in matplotlib?
# - Can we add sections to this height storage?
# - Can the algorithm easily index from 0?


# TODO instead of using the center point use a search to generate a continous path through the merged node
# When finding the final path:
# Store the exact entry point from the previous node.
# For each lake/ multi-point node encountered create a graph out of the grid where each edge in the grid is shorter if it's deeper.
# Surface edge is 2 units, deepest edge is one unit
# Find the shortest path from the entry node to the exit node.
# If there are multiple exit nodes then consider them all to be equal weight.


def enlarge_bounding_box_until_path_is_found(start_rowcol, end_rowcol, size_factors):

    window = generate_bounding_box(start_rowcol, end_rowcol, size_factors)
    start_window_rowcol = apply_window_to_rowcol(window, start_rowcol)
    end_window_rowcol = apply_window_to_rowcol(window, end_rowcol)

    height_raster = get_raster(window)

    graph = convert_to_graph(height_raster)
    # check_equal_height_nodes(height_raster, graph)
    graph = flood_low_points(graph, height_raster)
    # check_flooded_nodes(height_raster, graph)

    key_lookup = {k: key for key in graph.keys() for k in key}
    path = [key_lookup[start_window_rowcol]]
    for i in range(2000):
        current_point = path[-1]
        next_points = graph[current_point]
        if len(next_points) == 0:
            size_factors = detect_edge_touch(
                height_raster.shape, current_point, size_factors
            )
            print(f"Restarting with size factors {size_factors}")
            show_plot(
                height_raster,
                start_window_rowcol,
                end_window_rowcol,
                find_centerpoint(current_point),
                path,
            )
            return enlarge_bounding_box_until_path_is_found(
                start_rowcol, end_rowcol, size_factors
            )

        selected_point = min(
            next_points, key=lambda node_key: height_raster[node_key[0]]
        )
        path.append(selected_point)

        close_point, distance = distance_closest_point(
            end_window_rowcol, selected_point
        )
        if distance < 5:
            break
    else:
        # Reached path length limit and gave up
        return []

    print(f"Solution found with {distance=}")
    show_plot(height_raster, start_window_rowcol, end_window_rowcol, close_point, path)
    return path, height_raster


def generate_bounding_box(start_rowcol, end_rowcol, size_factors):
    # Generate a box which encloses the start and end point
    # Size factors stores where the bounding box needs to be larger than normal

    center_y = (start_rowcol[0] + end_rowcol[0]) // 2
    center_x = (start_rowcol[1] + end_rowcol[1]) // 2

    longest_dimension = max(
        abs(end_rowcol[0] - start_rowcol[0]), abs(end_rowcol[1] - start_rowcol[1])
    )
    edge_to_center = longest_dimension / 2

    top = int(max(0, center_y - edge_to_center * size_factors[0]))
    bottom = int(
        min(TIF_MAX_DIMENSIONS[0] - 1, center_y + edge_to_center * size_factors[1])
    )
    left = int(max(0, center_x - edge_to_center * size_factors[2]))
    right = int(
        min(TIF_MAX_DIMENSIONS[0] - 1, center_x + edge_to_center * size_factors[3])
    )
    # print(top, bottom, left, right, right - left, bottom - top)

    return rio.windows.Window(
        col_off=left,
        row_off=top,
        width=right - left,
        height=bottom - top,
    )


def measure_distance(path):
    path = [find_centerpoint(point) for point in path]
    distance = 0
    for point, next_point in zip(path, path[1:]):
        distance += (
            (point[0] - next_point[0]) ** 2 + (point[1] - next_point[1]) ** 2
        ) ** 0.5
    print(f"River distance {distance/100:.2f}km")


def elevation_profile(path, heights):
    distance = 0
    x = [0]
    y = [heights[path[0][0]]]
    for point, next_point in zip(path, path[1:]):
        centerpoint = find_centerpoint(point)
        next_centerpoint = find_centerpoint(next_point)
        distance += (
            (centerpoint[0] - next_centerpoint[0]) ** 2
            + (centerpoint[1] - next_centerpoint[1]) ** 2
        ) ** 0.5
        x.append(distance / 100)  # Distance in km
        y.append(heights[next_point[0]])
    plt.plot(x, y)
    plt.show()
    print(f"Avg gradient {(max(y)-min(y))/(distance/100):.0f}m/km")


if __name__ == "__main__":
    start_point = (-41.55327294639188, 145.87881557530164)  # Vale putin
    end_point = (-41.62953442116648, 145.7696457139196)  # Vale takeout
    # start_point = (-42.229119247079964, 145.81054340737677)  # Franklin putin
    # end_point = (-42.285970802829496, 145.74782103623605)  # Franklin midway
    path, heights = trace_and_expand_existing_graph(start_point, end_point)
    measure_distance(path)
    elevation_profile(path, heights)
