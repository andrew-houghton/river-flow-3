from pyproj import Proj
import rasterio
from pathlib import Path
import rasterio as rio
from matplotlib import pyplot as plt
from algorithms import convert_to_graph, flood_low_points
from pprint import pprint


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
    x,y = proj(lat, lon)
    x=x/10 - 30000
    y=550000 - y/10
    return int(x), int(y)

def row_col_to_lat_lon(x, y):
    x=(x + 30000)*10
    y=(55000 - y)*10
    return proj(x,y,inverse=True)

def start_finish_to_path(start_point, end_point):
    # Returns a list of lat longs with heights

    start_rowcol = lat_lon_to_row_col(*start_point)
    end_rowcol = lat_lon_to_row_col(*end_point)
    size_factors = [1.2,1.2,1.2,1.2]
    return enlarge_bounding_box_until_path_is_found(start_rowcol, end_rowcol, size_factors)

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
    x = sum(i[0] for i in node_key)/len(node_key)
    y = sum(i[1] for i in node_key)/len(node_key)
    return x, y


def enlarge_bounding_box_until_path_is_found(start_rowcol, end_rowcol, size_factors):
    window = generate_bounding_box(start_rowcol, end_rowcol, size_factors)
    start_window_rowcol = apply_window_to_rowcol(window, start_rowcol)
    end_window_rowcol = apply_window_to_rowcol(window, end_rowcol)

    height_raster = get_raster(window)
    graph = convert_to_graph(height_raster)
    graph = flood_low_points(graph, height_raster)
    # pprint(list(graph.keys())[0])
    # pprint(list(graph.values())[0])

    # Starting from start_window_rowcol start tracing a path
    # If there is branching select the lower point
    # If there is a tie select the further point (manhattan distance)
    # If there is still a tie then select at random
    # Move to next point and continue tracing the path

    # Finishing:
    # while distance to end is within a threshold then add current end point as a candidate
    # if distance ever goes back above the threshold then pick the best end candidate
    # if the path hits the end then exit early
    key_lookup = {k:key for key in graph.keys() for k in key}
    path = [key_lookup[start_window_rowcol]]
    for i in range(100):
        previous_point = path[-1]
        next_points = graph[previous_point]
        if len(next_points) == 0:
            break
        selected_point = min(next_points, key=lambda node_key: height_raster[node_key[0]])
        path.append(selected_point)

    plt.imshow(height_raster, cmap='winter')
    for i in range(len(path)-1):
        current_point = find_centerpoint(path[i])
        next_point = find_centerpoint(path[i+1])
        print(current_point)
        plt.plot(current_point, next_point)
    plt.show()

    # return trace_path(height_raster, start_window_rowcol, end_window_rowcol)

def generate_bounding_box(start_rowcol, end_rowcol, size_factors):
    # Generate a box which encloses the start and end point
    # Size factors stores where the bounding box needs to be larger than normal
    center_x = (start_rowcol[0]+end_rowcol[0])//2
    center_y = (start_rowcol[1]+end_rowcol[1])//2

    longest_dimension = max(end_rowcol[0]-start_rowcol[0], end_rowcol[1]-start_rowcol[1])
    edge_to_center = longest_dimension/2

    left = int(max(0, center_x - edge_to_center * size_factors[0]))
    top = int(max(0, center_y - edge_to_center * size_factors[1]))
    right = int(min(TIF_MAX_DIMENSIONS[0] - 1, center_x + edge_to_center * size_factors[2]))
    bottom = int(min(TIF_MAX_DIMENSIONS[0] - 1, center_y + edge_to_center * size_factors[3]))

    return rio.windows.Window(left, top, right-left, bottom-top)

if __name__ == '__main__':
    start_point = (147.086086,-41.448218)
    end_point = (147.122328,-41.443116)
    start_finish_to_path(start_point, end_point)