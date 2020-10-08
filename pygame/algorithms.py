# This file holds the base algorithms which manipulate the graph and do flow simulation
# It avoids dealing with UI and other concerns

from functools import partial
from collections import defaultdict


def check_nodes_equal_height(node_a, node_b, state, settings):
    return (
        settings.height_map[state.points[0][1] + node_a[1], state.points[0][0] + node_a[0]]
        == settings.height_map[state.points[0][1] + node_b[1], state.points[0][0] + node_b[0]]
    )


def equal_height_node_merge(state, settings):
    # If two nodes on the graph are the same height and adjacent then merge them into one node.
    # The reason for this is to allow flow to cross large flat sections
    # otherwise the water wouldn't know which wat to flow

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


def get_height_by_key(key, state):
    return state.selected_area_height_map[key[0][1], key[0][0]]

def does_node_touch_border(node, state):
    if node[0] == 0:
        return True
    if node[1] == 0:
        return True
    if node[0] == state.selection_pixel_size[0] - 1:
        return True
    if node[1] == state.selection_pixel_size[1] - 1:
        return True
    return False

def find_low_nodes(graph, state):


    low_nodes = []
    for node_key, adjacent_nodes in graph.items():
        if any(does_node_touch_border(node, state) for node in node_key):
            continue
        height = get_height_by_key(node_key, state)
        for adjacent_node_key in adjacent_nodes:
            if height > get_height_by_key(adjacent_node_key, state):
                break
        else:
            low_nodes.append(node_key)
    return low_nodes


def calculate_watershed(state, source=None):
    if source:
        node_flows = defaultdict(float)
        node_flows[source] = 1
    else:
        node_flows = {key: len(key) for key in state.graph}

    for node in sorted(state.graph, key=lambda node: get_height_by_key(node, state), reverse=True):
        if source is not None and node_flows[source] == 0:
            continue

        node_height = get_height_by_key(node, state)
        if not any(does_node_touch_border(i, state) for i in node):
            outflows = []
            for neighbour in state.graph[node]:
                neighbour_height = get_height_by_key(neighbour, state)
                if neighbour_height < node_height:
                    outflows.append((neighbour, node_height - neighbour_height))
            assert outflows

            total_outflow_height = sum(i[1] for i in outflows)
            for neighbour, outflow_height in outflows:
                node_flows[neighbour] += node_flows[node] * outflow_height / total_outflow_height

    return node_flows, None

def calculate_flow(state, num_cycles, source=None):
    if source:
        node_flows = {source: 1}
    else:
        node_flows = {key: len(key) for key in state.graph}

    yield node_flows

    for i in range(num_cycles):
        sorted_nodes = sorted(node_flows, key=lambda node: get_height_by_key(node, state))
        for node in sorted_nodes:
            node_height = get_height_by_key(node, state)
            if not any(does_node_touch_border(i, state) for i in node):
                outflows = []
                for neighbour in state.graph[node]:
                    neighbour_height = get_height_by_key(neighbour, state)
                    if neighbour_height < node_height:
                        outflows.append((neighbour, node_height - neighbour_height))
                assert outflows

                total_outflow_height = sum(i[1] for i in outflows)
                for neighbour, outflow_height in outflows:
                    if neighbour in node_flows:
                        node_flows[neighbour] += node_flows[node] * outflow_height / total_outflow_height
                    else:
                        node_flows[neighbour] = node_flows[node] * outflow_height / total_outflow_height
            del node_flows[node]
            if not node_flows:
                break
        yield node_flows
