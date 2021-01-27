from tqdm import tqdm
import heapq


def get_adjacent_nodes(grid_size, active_segments, y, x):
    output = []
    for point in ((y, x - 1), (y, x + 1), (y - 1, x), (y + 1, x)):
        point_segment = point[0] // grid_size, point[1] // grid_size
        if point_segment in active_segments:
            output.append(point)
    return output


def count_graph(graph):
    # For debugging
    num_nodes = 0
    num_points = 0
    for node in graph:
        num_nodes += 1
        num_points += len(node)
    print(f"{num_nodes=} {num_points=}")


def get_points_in_segment(segment, grid_size):
    return [
        (segment[0] * grid_size + y, segment[1] * grid_size + x)
        for x in range(grid_size)
        for y in range(grid_size)
    ]


def replace_tuple_value(original, old, new):
    return list(i for i in original if i != old) + [new]


def add_segment_to_graph(graph, heights, grid_size, added_segment, active_segments):
    from trace import show_heights

    print(
        f"Adding segment {added_segment[0]*grid_size}, {added_segment[1]*grid_size}. Size {grid_size}"
    )
    node_merge_operations = []
    skip_points = set()
    non_skip_points = []

    for point in tqdm(
        get_points_in_segment(added_segment, grid_size),
        desc="Finding equal height nodes via BFS",
    ):
        if point not in skip_points:
            height = heights[point]
            visited, queue = set(), [point]
            while queue:
                vertex = queue.pop(0)
                if vertex not in visited:
                    visited.add(vertex)
                    adjacent_nodes = get_adjacent_nodes(
                        grid_size, active_segments, *vertex
                    )
                    adjacent_equal_height = {
                        i for i in adjacent_nodes if heights[i] == height
                    }
                    queue.extend(adjacent_equal_height - visited - skip_points)

            if visited != {point}:
                node_merge_operations.append(visited)
                for node in visited:
                    skip_points.add(node)
            else:
                non_skip_points.append(point)

    # We have all the node merge operations
    key_lookup = {k: key for key in graph.keys() for k in key}
    node_merge_operations = [tuple(sorted(i)) for i in node_merge_operations]

    # Clear out any existing points on the graph which include these points
    # Update key lookup to use the new node_keys

    for node_key in node_merge_operations:
        assert (
            node_key not in graph
        ), "Node merging operation not required if merged key already exists"
        for point in node_key:
            if key_lookup.get(point) in graph:
                del graph[key_lookup[point]]
            key_lookup[point] = node_key

    isolated_new_points = set(get_points_in_segment(added_segment, grid_size))
    isolated_new_points -= {j for i in node_merge_operations for j in i}
    new_nodes_to_add = node_merge_operations + [(i,) for i in isolated_new_points]

    # Now go through each new node
    # Find it's neighbours
    # Create entries in the graph which link the neighbours
    for node_key in new_nodes_to_add:
        neighbours = set()
        for point in node_key:
            adjacent_points = get_adjacent_nodes(grid_size, active_segments, *point)
            for adjacent_point in adjacent_points:
                if adjacent_point not in node_key:
                    neighbours.add(key_lookup.get(adjacent_point, (adjacent_point,)))
        graph[node_key] = neighbours

    return graph


def does_node_touch_border(active_segments, grid_size, point):
    if (point[0] // grid_size, (point[1] - 1) // grid_size) not in active_segments:
        return True
    if (point[0] // grid_size, (point[1] + 1) // grid_size) not in active_segments:
        return True
    if ((point[0] - 1) // grid_size, point[1] // grid_size) not in active_segments:
        return True
    if ((point[0] + 1) // grid_size, point[1] // grid_size) not in active_segments:
        return True
    return False


def generate_existing_points_touching_new_segment(
    grid_size, added_segment, active_segments
):
    output = []
    if (added_segment[0] - 1, added_segment[1]) in active_segments:
        # segment above
        output += [
            (added_segment[0] * grid_size - 1, added_segment[1] * grid_size + i)
            for i in range(grid_size)
        ]
    if (added_segment[0] + 1, added_segment[1]) in active_segments:
        # segment below
        output += [
            ((added_segment[0] + 1) * grid_size, added_segment[1] * grid_size + i)
            for i in range(grid_size)
        ]
    if (added_segment[0], added_segment[1] - 1) in active_segments:
        # segment left
        output += [
            (added_segment[0] * grid_size + i, added_segment[1] * grid_size - 1)
            for i in range(grid_size)
        ]
    if (added_segment[0], added_segment[1] + 1) in active_segments:
        output += [
            (added_segment[0] * grid_size + i, (added_segment[1] + 1) * grid_size)
            for i in range(grid_size)
        ]
    return output


def flood_added_segment(graph, heights, grid_size, added_segment, active_segments):
    low_nodes = []
    key_lookup = {k: key for key in graph.keys() for k in key}

    nodes_which_could_be_low_points = {
        key_lookup[adjacent_point]
        for point in get_points_in_segment(added_segment, grid_size)
        for adjacent_point in get_adjacent_nodes(grid_size, active_segments, *point)
    }

    existing_points_which_could_be_low = generate_existing_points_touching_new_segment(
        grid_size, added_segment, active_segments
    )
    existing_nodes_which_could_be_low = [
        key_lookup[point] for point in existing_points_which_could_be_low
    ]
    nodes_which_could_be_low_points.update(existing_nodes_which_could_be_low)

    for node_key in nodes_which_could_be_low_points:
        adjacent_nodes = graph[node_key]
        if any(
            does_node_touch_border(active_segments, grid_size, point)
            for point in node_key
        ):
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
            if any(
                does_node_touch_border(active_segments, grid_size, point)
                for point in node
            ):
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

        # merged_node_key is the new node key. It includes all the nodes in merging_nodes
        #

        for neighbour in neighbours:
            updated_neighbours = graph[neighbour] - merging_nodes
            updated_neighbours.add(merged_node_key)
            graph[neighbour] = updated_neighbours
        graph[merged_node_key] = set(neighbours)
        heights[merged_node_key[0]] = lake_height

        for merging_node in merging_nodes:
            del graph[merging_node]

    assert False
    return graph
