from functools import partial
from collections import defaultdict


def check_nodes_equal_height(node_a, node_b, state, settings):
    return (
        settings.height_map[state.points[0][1] + node_a[1], state.points[0][0] + node_a[0]]
        == settings.height_map[state.points[0][1] + node_b[1], state.points[0][0] + node_b[0]]
    )


def equal_height_node_merge(state, settings):
    from animations import _get_adjacent_nodes

    node_merge_operations = []
    skip_nodes = set()
    node_check_func = partial(check_nodes_equal_height, state=state, settings=settings)
    for x in range(state.selection_pixel_size[0]):
        for y in range(state.selection_pixel_size[1]):
            if (x, y) not in skip_nodes:
                height = settings.height_map[state.points[0][1] + y, state.points[0][0] + x]

                visited, queue = set(), [(x, y)]
                while queue:
                    vertex = queue.pop(0)
                    if vertex not in visited:
                        visited.add(vertex)
                        queue.extend(set(_get_adjacent_nodes(vertex, state, node_check_func)) - visited - skip_nodes)

                if visited != {(x, y)}:
                    node_merge_operations.append(visited)
                    for node in visited:
                        skip_nodes.add(node)

    node_movements = {}
    for merging_nodes in node_merge_operations:
        new_location = (
            sum(x for x, y in merging_nodes) / len(merging_nodes),
            sum(y for x, y in merging_nodes) / len(merging_nodes),
        )
        for node in merging_nodes:
            node_movements[node] = new_location
    return node_movements, skip_nodes, node_merge_operations


def create_graph(node_merge_operations, skip_nodes, non_skip_nodes, state):
    from animations import _get_adjacent_nodes

    # For every original position
    # Lookup the current positions new key

    # Loop through the adjacent nodes
    # Find the new keys for those adjacent nodes

    # Filter out all adjacent nodes which have the same key as the current node
    # Add an edge to the adjacent new nodes

    graph = defaultdict(list)
    new_key = {}
    for merging_nodes in node_merge_operations:
        for node in merging_nodes:
            new_key[node] = tuple(sorted(merging_nodes))

    for node in sorted(list(skip_nodes) + non_skip_nodes):
        node_key = new_key.get(node, (node,))

        adjacent_nodes = _get_adjacent_nodes(node, state)
        for adjacent_node in adjacent_nodes:
            adjacent_node_key = new_key.get(adjacent_node, (adjacent_node,))
            if adjacent_node_key != node_key:
                graph[node_key].append(adjacent_node_key)

    return dict(graph)
