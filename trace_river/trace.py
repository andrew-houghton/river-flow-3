from pathlib import Path

import numpy as np
import rasterio as rio
from matplotlib import pyplot as plt
from pyproj import Proj

from path_tracing import align_path, find_point_track
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
GRID = 200
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
        return height_raster


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
    # check_equal_height_nodes(graph, heights, active_segments, GRID)
    graph, heights = flood_added_segment(
        graph, heights, GRID, next_segment, active_segments
    )
    # check_flooded_nodes(graph, heights, active_segments, GRID)

    key_lookup = {k: key for key in graph.keys() for k in key}
    path = [key_lookup[start_rowcol]]
    assert key_lookup[start_rowcol] in graph
    track_data = {}

    closest_finish_node = None
    finish_point_threshold = 50
    plt.get_current_fig_manager().full_screen_toggle()
    plt.ion()
    plt.show()
    for i in range(10000):
        current_node = key_lookup[path[-1][0]]
        next_nodes = graph[current_node]
        next_segment = detect_edge_touch(
            current_node,
            active_segments,
            GRID,
        )

        if next_segment:
            track_data = find_point_track(heights, path, start_rowcol, track_data)
            show_plot(
                heights,
                path,
                track_data,
                active_segments,
                GRID,
                start_rowcol,
                end_rowcol,
            )

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
            # check_equal_height_nodes(graph, heights, active_segments, GRID)
            graph, heights = flood_added_segment(
                graph, heights, GRID, next_segment, active_segments
            )
            # check_flooded_nodes(graph, heights, active_segments, GRID)
            key_lookup = {k: key for key in graph.keys() for k in key}
            path = align_path(graph, key_lookup, path)
            current_node = path[-1]
            continue

        selected_node = min(next_nodes, key=lambda node_key: heights[node_key[0]])
        distance = distance_closest_point(end_rowcol, selected_node)
        if closest_finish_node is None:
            if distance < finish_point_threshold:
                closest_finish_node = selected_node
        else:
            if distance > distance_closest_point(end_rowcol, closest_finish_node):
                # We're getting further away so just finish without the last point
                # TODO terminate path at closest_finish_node
                plt.ioff()
                track_data = find_point_track(heights, path, start_rowcol, track_data)
                show_plot(
                    heights,
                    path,
                    track_data,
                    active_segments,
                    GRID,
                    start_rowcol,
                    end_rowcol,
                )
                plt.show()
                return path, heights
            else:
                closest_finish_node = selected_node

        path.append(selected_node)

    print("Algorithm passed iteration limit")
    return path, heights


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


def show_plot(heights, path, track_data, active_segments, grid_size, start, end):
    min_height = None
    for segment in active_segments:
        segment_min = heights[
            segment[0] * GRID : segment[0] * GRID + GRID,
            segment[1] * GRID : segment[1] * GRID + GRID,
        ].min()
        if min_height is None or segment_min < min_height:
            min_height = segment_min

    min_y = min(i[0] * grid_size for i in active_segments)
    max_y = max((i[0] + 1) * grid_size for i in active_segments)
    min_x = min(i[1] * grid_size for i in active_segments)
    max_x = max((i[1] + 1) * grid_size for i in active_segments)

    plt.cla()
    selected_heights = heights[min_y:max_y, min_x:max_x]
    plt.imshow(selected_heights)
    plt.clim(min_height, heights.max())
    for node, dest_node in zip(path, path[1:]):
        for point in track_data[(node, dest_node)]:
            point = point[0] - min_y, point[1] - min_x
            plt.plot(point[1], point[0], "yo", markersize=1)

    plt.plot(start[1] - min_x, start[0] - min_y, "ro")
    if (end[0] // grid_size, end[1] // grid_size) in active_segments:
        plt.plot(end[1] - min_x, end[0] - min_y, "bo")

    plt.draw()
    plt.pause(0.001)


def distance_closest_point(end, node_key):
    return min(abs(end[0] - x[0]) + abs(end[1] - x[1]) for x in node_key)


def measure_distance(path):
    path = [find_centerpoint(point) for point in path]
    distance = 0
    for point, next_point in zip(path, path[1:]):
        distance += (
            (point[0] - next_point[0]) ** 2 + (point[1] - next_point[1]) ** 2
        ) ** 0.5
    return f"River distance {distance/100:.2f}km"


def elevation_profile(path, heights, dist_string=None):
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
    fig_text = f"Avg gradient {(max(y)-min(y))/(distance/100):.0f}m/km"
    if dist_string:
        fig_text += "\n"
        fig_text += dist_string
    plt.figtext(0.5, 0.01, fig_text, ha="center", fontsize=18, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})
    plt.get_current_fig_manager().full_screen_toggle()

    plt.show()

if __name__ == "__main__":
    start_point = (-41.55327294639188, 145.87881557530164)  # Vale putin
    end_point = (-41.62953442116648, 145.7696457139196)  # Vale takeout
    # start_point = (-42.229119247079964, 145.81054340737677)  # Franklin putin
    # end_point = (-42.285970802829496, 145.74782103623605)  # Franklin midway
    path, heights = trace_and_expand_existing_graph(start_point, end_point)
    dist_string = measure_distance(path)
    elevation_profile(path, heights, dist_string)
