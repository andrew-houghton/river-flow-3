from algorithms import get_adjacent_nodes, does_node_touch_border
from tqdm import tqdm


def check_equal_height_nodes(heights, graph):
    # For every node check that it's connected to it's equal height neighbours
    # and adjacent to it's different height neighbours
    # Also check that all expected nodes are included
    key_lookup = {k: key for key in graph.keys() for k in key}
    visited = set()
    for point, node_key in tqdm(key_lookup.items(), desc="Checking node connections"):
        visited.add(point)
        for neighbour in get_adjacent_nodes(heights, *point):
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
        (x, y) for x in range(heights.shape[0]) for y in range(heights.shape[1])
    }
    assert expected_visited == visited, "Every node should be visited"


def check_flooded_nodes(heights, graph):
    # for every node key check that it's either on the border
    # or higher than all it's neighbours
    # check no nodes are missing
    expected_visited = {
        (x, y) for x in range(heights.shape[0]) for y in range(heights.shape[1])
    }
    visited = set()
    for node_key, neighbours in tqdm(graph.items(), "checking node flooding"):
        current_height = heights[node_key[0]]
        for node in node_key:
            visited.add(node)
        if not any(does_node_touch_border(heights.shape, node) for node in node_key):
            # This node should not have lower height neighbours
            assert any(
                heights[neighbour[0]] < current_height for neighbour in neighbours
            ), "A neighbour must be lower"

    assert expected_visited == visited, "Every node should be visited"
