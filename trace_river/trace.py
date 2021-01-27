from pathlib import Path

import numpy as np
import rasterio as rio
from matplotlib import pyplot as plt
from pyproj import Proj

from algorithms import add_segment_to_graph, flood_added_segment
from graph import Graph
from graph_verify import check_equal_height_nodes, check_flooded_nodes, do_keys_overlap

proj_string = "+proj=utm +zone=55 +south +datum=WGS84 +units=m +no_defs"
proj = Proj(proj_string)
heights_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "heights.tif")
)
colour_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour.tif")
)
TIF_MAX_DIMENSIONS = (30978, 30978)
GRID = 5
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
        height_raster = heights.read(1, window=window)
        # print(height_raster)
        return height_raster


def show_heights(heights, graph, active_segments, grid_size):
    min_y = min(i[0] * grid_size for i in active_segments)
    max_y = max((i[0] + 1) * grid_size for i in active_segments)
    min_x = min(i[1] * grid_size for i in active_segments)
    max_x = max((i[1] + 1) * grid_size for i in active_segments)
    print(heights[min_y:max_y, min_x:max_x])

    nodes = np.zeros((max_y - min_y, max_x - min_x), dtype=np.int16)
    for i, nk in enumerate(graph):
        for j in nk:
            nodes[j[0] - min_y, j[1] - min_x] = i
    # Print with layout matching above numbers
    for row in range(max_y - min_y):
        print(" [", end="")
        for col in range(max_x - min_x):
            print(f"{nodes[row, col]: <4}", end="")
        print("]")


def trace_and_expand_existing_graph(start_point, end_point):
    start_rowcol = lat_lon_to_row_col(*start_point)
    end_rowcol = lat_lon_to_row_col(*end_point)

    next_segment = (start_rowcol[0] // GRID, start_rowcol[1] // GRID)
    print(f"Starting with segment {next_segment}")
    active_segments = [next_segment]
    heights = np.zeros(TIF_MAX_DIMENSIONS, dtype=np.int16)
    heights[
        next_segment[0] * GRID : next_segment[0] * GRID + GRID,
        next_segment[1] * GRID : next_segment[1] * GRID + GRID,
    ] = get_raster(next_segment)

    graph = Graph()
    graph = add_segment_to_graph(graph, heights, GRID, next_segment, active_segments)
    check_equal_height_nodes(graph, heights, active_segments, GRID)
    graph = flood_added_segment(graph, heights, GRID, next_segment, active_segments)
    check_flooded_nodes(graph, heights, active_segments, GRID)

    key_lookup = {k: key for key in graph.keys() for k in key}
    path = [key_lookup[start_rowcol]]
    assert key_lookup[start_rowcol] in graph

    closest_finish_point = None
    finish_point_threshold = 10

    for i in range(10000):
        current_node = path[-1]
        current_node = key_lookup[current_node[0]]
        next_nodes = graph[current_node]
        next_segment = detect_edge_touch(
            current_node,
            active_segments,
            GRID,
        )

        if next_segment:
            do_keys_overlap(graph)
            print(f"Adding segment {next_segment}")
            active_segments.append(next_segment)
            heights[
                next_segment[0] * GRID : next_segment[0] * GRID + GRID,
                next_segment[1] * GRID : next_segment[1] * GRID + GRID,
            ] = get_raster(next_segment)
            graph = add_segment_to_graph(
                graph, heights, GRID, next_segment, active_segments
            )
            check_equal_height_nodes(graph, heights, active_segments, GRID)
            show_heights(heights, graph, active_segments, GRID)
            graph = flood_added_segment(
                graph, heights, GRID, next_segment, active_segments
            )
            show_heights(heights, graph, active_segments, GRID)
            check_flooded_nodes(graph, heights, active_segments, GRID)
            key_lookup = {k: key for key in graph.keys() for k in key}
            continue

        selected_node = min(next_nodes, key=lambda node_key: heights[node_key[0]])
        distance = distance_closest_point(end_rowcol, selected_node)
        closest_finish_node = None
        if closest_finish_node is not None:
            if distance > distance_closest_point(end_rowcol, closest_finish_node):
                # We're getting further away so just finish without the last point
                break
            else:
                closest_finish_node = selected_node
        elif distance < finish_point_threshold:
            closest_finish_node = selected_node

        path.append(selected_node)

    print("Algorithm passed iteration limit")
    return path, heights


def apply_window_to_rowcol(window, rowcol):
    # Convert co-ordinates to be relative to a window
    return rowcol[0] - window.row_off, rowcol[1] - window.col_off


def find_centerpoint(node_key):
    x = sum(i[0] for i in node_key) / len(node_key)
    y = sum(i[1] for i in node_key) / len(node_key)
    return x, y


def detect_edge_touch(node, active_segments, grid_size):
    # This function should instead return the segment which should be added
    for point in node:
        for offset in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            offset_point_segment = (
                (point[0] + offset[0]) // grid_size,
                (point[1] + offset[1]) // grid_size,
            )
            if offset_point_segment not in active_segments:
                return offset_point_segment


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
    return min(abs(end[0] - x[0]) + abs(end[1] - x[1]) for x in node_key)


# TODO instead of using the center point use a search to generate a continous path through the merged node
# When finding the final path:
# Store the exact entry point from the previous node.
# For each lake/ multi-point node encountered create a graph out of the grid where each edge in the grid is shorter if it's deeper.
# Surface edge is 2 units, deepest edge is one unit
# Find the shortest path from the entry node to the exit node.
# If there are multiple exit nodes then consider them all to be equal weight.


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
    # from ipdb import launch_ipdb_on_exception
    # with launch_ipdb_on_exception():
    path, heights = trace_and_expand_existing_graph(start_point, end_point)
    measure_distance(path)
    elevation_profile(path, heights)
