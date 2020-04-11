from functools import partial


def check_nodes_equal_height(node_a, node_b, state, settings):
    return (
        settings.height_map[state.points[0][1] + node_a[1], state.points[0][0] + node_a[0]]
        == settings.height_map[state.points[0][1] + node_b[1], state.points[0][0] + node_b[0]]
    )


def equal_height_node_merge(state, settings):
    from animations import get_adjacent_nodes
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
                        queue.extend(set(get_adjacent_nodes(vertex, state, node_check_func)) - visited - skip_nodes)

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
    return node_movements, skip_nodes
