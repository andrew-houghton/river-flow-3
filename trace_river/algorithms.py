from tqdm import tqdm
from collections import defaultdict
import heapq


def get_adjacent_nodes(heights, x, y):
    output = []
    for point in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)):
        if point[0] < heights.shape[0] and point[0] >= 0:
            if point[1] < heights.shape[1] and point[1] >= 0:
                output.append(point)
    return output


def convert_to_graph(heights):
    node_merge_operations = []
    skip_nodes = set()
    non_skip_nodes = []
    # node_check_func = partial(check_nodes_equal_height, state=state, settings=settings)
    for x in tqdm(
        range(heights.shape[0]), desc="Processing rows for equal height merge"
    ):
        for y in range(heights.shape[1]):
            if (x, y) not in skip_nodes:
                height = heights[x, y]
                visited, queue = set(), [(x, y)]
                while queue:
                    vertex = queue.pop(0)
                    if vertex not in visited:
                        visited.add(vertex)
                        adjacent_nodes = get_adjacent_nodes(heights, *vertex)
                        adjacent_equal_height = {
                            i for i in adjacent_nodes if heights[i] == height
                        }
                        queue.extend(adjacent_equal_height - visited - skip_nodes)

                if visited != {(x, y)}:
                    node_merge_operations.append(visited)
                    for node in visited:
                        skip_nodes.add(node)
                else:
                    non_skip_nodes.append((x, y))

    graph = defaultdict(list)
    new_key = {}
    for merging_nodes in tqdm(node_merge_operations, desc="Creating new merged nodes"):
        sorted_merging_nodes = tuple(sorted(merging_nodes))
        for node in merging_nodes:
            new_key[node] = sorted_merging_nodes

    for node in tqdm(
        sorted(list(skip_nodes) + non_skip_nodes), desc="Processing other nodes"
    ):
        node_key = new_key.get(node, (node,))

        adjacent_nodes = get_adjacent_nodes(heights, *node)
        for adjacent_node in adjacent_nodes:
            adjacent_node_key = new_key.get(adjacent_node, (adjacent_node,))
            if adjacent_node_key != node_key:
                graph[node_key].append(adjacent_node_key)

    return dict(graph)


def does_node_touch_border(shape, node):
    return (
        node[0] == 0
        or node[1] == 0
        or node[0] == shape[0] - 1
        or node[1] == shape[1] - 1
    )


def flood_low_points(graph, heights):
    low_nodes = []
    for node_key, adjacent_nodes in graph.items():
        if any(does_node_touch_border(heights.shape, node) for node in node_key):
            continue
        height = heights[node_key[0]]
        for adjacent_node_key in adjacent_nodes:
            if height > heights[adjacent_node_key[0]]:
                break
        else:
            low_nodes.append(node_key)

    if not low_nodes:
        return graph

    for low_node in low_nodes:
        if low_node not in graph:
            continue

        lake_height = heights[low_node[0]]
        for neighbour in graph[low_node]:
            if heights[neighbour[0]] < lake_height:
                continue
        queue = [(lake_height, low_node)]
        nodes_in_queue = {low_node}
        merging_nodes = {low_node}

        while True:
            try:
                node_height, node = heapq.heappop(queue)
            except IndexError:
                print("heap ran out of items but it shouldn't")
                break
            if node_height < lake_height:
                break
            lake_height = node_height
            merging_nodes.add(node)
            if any(does_node_touch_border(heights.shape, i) for i in node):
                break
            for adjacent_node in graph[node]:
                if adjacent_node not in nodes_in_queue:
                    nodes_in_queue.add(adjacent_node)
                    heapq.heappush(queue, (heights[adjacent_node[0]], adjacent_node))

        # Add all equal height nodes
        while True:
            try:
                node_height, node = heapq.heappop(queue)
            except IndexError:
                break

            # Don't merge the outflow points to the lake
            if node_height < lake_height:
                continue
            elif node_height == lake_height:
                merging_nodes.add(node)
                for adjacent_node in graph[node]:
                    if adjacent_node not in nodes_in_queue:
                        nodes_in_queue.add(adjacent_node)
                        heapq.heappush(
                            queue, (heights[adjacent_node[0]], adjacent_node)
                        )
            else:
                break
        merged_node_key = tuple(
            sorted({node for node_key in merging_nodes for node in node_key})
        )
        neighbours = {
            node for merging_node in merging_nodes for node in graph[merging_node]
        } - set(merging_nodes)
        for neighbour in neighbours:
            updated_neighbours = set(graph[neighbour]) - merging_nodes
            updated_neighbours.add(merged_node_key)
            graph[neighbour] = tuple(sorted(updated_neighbours))
        graph[merged_node_key] = tuple(sorted(neighbours))
        heights[merged_node_key[0]] = lake_height

        for merging_node in merging_nodes:
            del graph[merging_node]

    # Remove outflow for edge nodes
    for node_key in graph:
        if any(does_node_touch_border(heights.shape, node) for node in node_key):
            graph[node_key] = []

    return graph
