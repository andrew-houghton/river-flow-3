from algorithms import get_adjacent_nodes, does_node_touch_border, get_points_in_segment
from tqdm import tqdm


def check_equal_height_nodes(graph, heights, active_segments, grid_size):
    # For every node check that it's connected to it's equal height neighbours
    # and adjacent to it's different height neighbours
    # Also check that all expected nodes are included
    key_lookup = {k: key for key in graph.keys() for k in key}
    visited = set()
    for point, node_key in tqdm(key_lookup.items(), desc="Checking node connections"):
        visited.add(point)
        for neighbour in get_adjacent_nodes(grid_size, active_segments, *point):
            if heights[point] == heights[neighbour]:
                assert (
                    key_lookup[neighbour] == node_key
                ), "Adjacent equal height should be merged"
            else:
                touching_nodes = {j for i in graph[node_key] for j in i}
                assert (
                    neighbour in touching_nodes
                ), "Neighbour node should be connected in graph"

    expected_visited = {
        point
        for segment in active_segments
        for point in get_points_in_segment(segment, grid_size)
    }
    assert expected_visited == visited, "Every node should be visited"


def check_flooded_nodes(graph, heights, active_segments, grid_size):
    # for every node key check that it's either on the border
    # or higher than all it's neighbours
    # nodes which do touch the border should have no outflow nodes
    # check no nodes are missing
    visited = set()
    for node_key, neighbours in tqdm(graph.items(), "checking node flooding"):
        current_height = heights[node_key[0]]
        for node in node_key:
            visited.add(node)
        if not any(
            does_node_touch_border(active_segments, grid_size, point)
            for point in node_key
        ):
            # This node should not have lower height neighbours
            assert any(
                heights[neighbour[0]] < current_height for neighbour in neighbours
            ), "A neighbour must be lower"

    expected_visited = {
        point
        for segment in active_segments
        for point in get_points_in_segment(segment, grid_size)
    }
    assert expected_visited == visited, "Every node should be visited"
