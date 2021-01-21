from pyproj import Proj
import rasterio
from pathlib import Path
import rasterio as rio
from matplotlib import pyplot as plt
from algorithms import convert_to_graph, flood_low_points
from pprint import pprint
from graph_verify import check_equal_height_nodes, check_flooded_nodes

proj_string = "+proj=utm +zone=55 +south +datum=WGS84 +units=m +no_defs"
proj = Proj(proj_string)
heights_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "heights.tif")
)
colour_tif_path = (
    Path(__name__).absolute().parent.parent.joinpath("tasmania", "colour.tif")
)
TIF_MAX_DIMENSIONS = (30978, 30978)
assert heights_tif_path.exists()


def lat_lon_to_row_col(lat, lon):
    # Note: rounds to nearest point
    x, y = proj(lat, lon)
    x = x / 10 - 30000
    y = 550000 - y / 10
    return int(x), int(y)


def row_col_to_lat_lon(x, y):
    x = (x + 30000) * 10
    y = (55000 - y) * 10
    return proj(x, y, inverse=True)


def start_finish_to_path(start_point, end_point):
    # Returns a list of lat longs with heights

    start_rowcol = lat_lon_to_row_col(*start_point)
    end_rowcol = lat_lon_to_row_col(*end_point)
    size_factors = [1.2, 1.2, 1.2, 1.2]
    return enlarge_bounding_box_until_path_is_found(
        start_rowcol, end_rowcol, size_factors
    )


def apply_window_to_rowcol(window, rowcol):
    # Convert co-ordinates to be relative to a window
    return rowcol[0] - window.col_off, rowcol[1] - window.row_off


def get_raster(window, map_type="height"):
    if map_type == "height":
        with rio.open(heights_tif_path) as heights:
            return heights.read(1, window=window)
    else:
        raise Exception("Not implemented")


def find_centerpoint(node_key):
    x = sum(i[0] for i in node_key) / len(node_key)
    y = sum(i[1] for i in node_key) / len(node_key)
    return x, y


def detect_edge_touch(shape, node, size_factors):
    enlarge = [False, False, False, False]
    for point in node:
        if point[0] == 0:
            enlarge[1] = True
        if point[1] == 0:
            enlarge[0] = True
        if point[0] >= shape[0] - 1:
            enlarge[3] = True
        if point[1] >= shape[1] - 1:
            enlarge[2] = True
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


def enlarge_bounding_box_until_path_is_found(start_rowcol, end_rowcol, size_factors):
    # Starting from start_window_rowcol start tracing a path
    # If there is branching select the lower point
    # If there is a tie select the further point (manhattan distance)
    # If there is still a tie then select at random
    # Move to next point and continue tracing the path

    # Finishing:
    # while distance to end is within a threshold then add current end point as a candidate
    # if distance ever goes back above the threshold then pick the best end candidate
    # if the path hits the end then exit early

    window = generate_bounding_box(start_rowcol, end_rowcol, size_factors)
    start_window_rowcol = apply_window_to_rowcol(window, start_rowcol)
    end_window_rowcol = apply_window_to_rowcol(window, end_rowcol)
    start_window_rowcol = start_window_rowcol[1], start_window_rowcol[0]

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
            # show_plot(
            #     height_raster,
            #     start_window_rowcol,
            #     find_centerpoint(current_point),
            #     path,
            # )
            return enlarge_bounding_box_until_path_is_found(
                start_rowcol, end_rowcol, size_factors
            )

        selected_point = min(
            next_points, key=lambda node_key: height_raster[node_key[0]]
        )
        path.append(selected_point)

        close_point, distance = distance_closest_point(end_window_rowcol, selected_point)
        print(distance)
        if distance < 20:
            break
    else:
        # Reached path length limit and gave up
        return []

    print("Solution found")
    show_plot(height_raster, start_window_rowcol, end_window_rowcol, close_point, path)
    return path


def generate_bounding_box(start_rowcol, end_rowcol, size_factors):
    # Generate a box which encloses the start and end point
    # Size factors stores where the bounding box needs to be larger than normal
    center_x = (start_rowcol[0] + end_rowcol[0]) // 2
    center_y = (start_rowcol[1] + end_rowcol[1]) // 2

    longest_dimension = max(
        abs(end_rowcol[0] - start_rowcol[0]), abs(end_rowcol[1] - start_rowcol[1])
    )
    edge_to_center = longest_dimension / 2

    left = int(max(0, center_x - edge_to_center * size_factors[0]))
    top = int(max(0, center_y - edge_to_center * size_factors[1]))
    right = int(
        min(TIF_MAX_DIMENSIONS[0] - 1, center_x + edge_to_center * size_factors[2])
    )
    bottom = int(
        min(TIF_MAX_DIMENSIONS[0] - 1, center_y + edge_to_center * size_factors[3])
    )

    return rio.windows.Window(left, top, right - left, bottom - top)


if __name__ == "__main__":
    start_point = (147.086086, -41.448218)
    end_point = (147.120220, -41.443814)
    start_finish_to_path(start_point, end_point)
