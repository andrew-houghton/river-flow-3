import heapq


def get_adjacent_points(point):
    return [
        (point[0] - 1, point[1]),
        (point[0] + 1, point[1]),
        (point[0], point[1] - 1),
        (point[0], point[1] + 1),
    ]


def find_exit_point(node, dest_node, heights):
    best_point = None
    best_point_height = None
    dest_point_set = set(dest_node)

    for point in node:
        if any(neighbour in dest_point_set for neighbour in get_adjacent_points(point)):
            if best_point is None or heights[point] < best_point_height:
                best_point = point
                best_point_height = heights[point]
    assert (
        best_point is not None
    ), "There should be a point which is adjacent to the other node"
    return best_point


def find_deep_path(points, entry_point, exit_point, heights):
    distances = {point: float("infinity") for point in points}
    distances[entry_point] = 0

    point_set = set(points)
    point_set.add(entry_point)
    assert exit_point in point_set
    assert any(
        i in point_set for i in get_adjacent_points(entry_point) if i in point_set
    )

    pq = [(0, entry_point, [])]
    while len(pq) > 0:
        current_distance, point, path_to_point = heapq.heappop(pq)

        if point == exit_point:
            return path_to_point

        # Points can get added to the priority queue multiple times. We only
        # process a point the first time we remove it from the priority queue.
        if current_distance > distances[point]:
            continue

        adjacent_points = [i for i in get_adjacent_points(point) if i in point_set]
        # TODO get edge weights For now hard coded to one
        for neighbor in adjacent_points:
            weight = 1
            distance = current_distance + weight

            # Only consider this new path if it's better than any path we've
            # already found.
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                new_path = path_to_point.copy()
                new_path.append(neighbor)
                heapq.heappush(pq, (distance, neighbor, new_path))

    raise Exception("exit point not visited in search")


def find_point_track(heights, path, start_point, track_data):
    entry_point = start_point
    for node, dest_node in zip(path, path[1:]):
        track_key = (node, dest_node)
        if track_key in track_data:
            # The last point in the previous track is where the next point should start
            entry_point = track_data[track_key][-1]
        else:
            exit_point = find_exit_point(node, dest_node, heights)
            track = find_deep_path(node, entry_point, exit_point, heights)
            assert all(
                i in node for i in track
            ), "Track must only include points in the node"
            assert track[-1] == exit_point, "Track must finish at exit point"
            track_data[track_key] = track
            entry_point = exit_point
    print(f"{len(path)=} {len(track_data)=}")
    return track_data


def align_path(graph, key_lookup, path):
    already_in_path = set()
    fixed_path = []
    for node in path:
        if node not in graph:
            new_node = key_lookup[node[0]]
            if new_node not in already_in_path:
                already_in_path.add(new_node)
                fixed_path.append(new_node)
        else:
            if node not in already_in_path:
                already_in_path.add(node)
                fixed_path.append(node)
    return fixed_path
