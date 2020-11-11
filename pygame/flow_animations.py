import pygame
import random
from algorithms import equal_height_node_merge, create_graph, find_low_nodes
import heapq
from functools import lru_cache
import tqdm


def starting_image(screen, state, settings):
    image_size = settings.pygame_colour_image.get_rect().size
    state.resized_image_position = (
        (settings.screen_size[0] - image_size[0]) // 2,
        (settings.screen_size[1] - image_size[1]) // 2,
    )
    screen.fill((0,0,0))
    screen.blit(settings.pygame_colour_image, state.resized_image_position)
    if state.rectangle_bounds:
        pygame.draw.polygon(
            screen,
            settings.selection_line_colour,
            state.rectangle_bounds,
            settings.selection_line_width,
        )
    yield

def show_selection(screen, state, settings):
    if not state.scaled_location:
        state.scaled_location = (
            random.randint(0, settings.full_size_dimensions[0] - settings.screen_size[0] - 1),
            random.randint(0, settings.full_size_dimensions[1] - settings.screen_size[1] - 1),
        )
    state.selected_image = settings.get_image_window(state.scaled_location[0], state.scaled_location[1])
    screen.blit(state.selected_image, (0, 0))
    yield

def show_selection_height(screen, state, settings):
    state.selected_height = settings.get_image_window(state.scaled_location[0], state.scaled_location[1], mode="height")
    screen.blit(state.selected_height, (0, 0))
    yield

@lru_cache(maxsize=10000)
def get_node_centerpoint(node):
    return (sum(x for x, _ in node) / len(node), sum(y for _, y in node) / len(node))

def get_height_by_key(key, state):
    return state.selected_area_height_map[key[0][1], key[0][0]]

def graph_construction_progress(screen, state, settings):
    state.selection_pixel_size = settings.screen_size
    settings.height_map = settings.get_image_window(state.scaled_location[0], state.scaled_location[1], mode="numpy")
    state.selected_area_height_map = settings.height_map
    state.points = ((0, 0), (settings.screen_size[0], 0), (0, settings.screen_size[1]), (settings.screen_size[0], settings.screen_size[1]))
    yield
    
    _, skip_nodes, node_merge_operations = equal_height_node_merge(state, settings)
    screen.fill((0,0,0))
    yield

    non_skip_nodes = [
        (x, y)
        for x in range(state.selection_pixel_size[0])
        for y in range(state.selection_pixel_size[1])
        if (x, y) not in skip_nodes
    ]

    state.graph = create_graph(node_merge_operations, skip_nodes, non_skip_nodes, state)
    screen.fill((200,200,200))
    yield

    state.low_nodes = sorted(find_low_nodes(state.graph, state), key=lambda key: get_height_by_key(key, state))
    screen.fill((200,200,200))
    yield


    def does_node_touch_border(node):
        if node[0] == 0:
            return True
        if node[1] == 0:
            return True
        if node[0] == state.selection_pixel_size[0] - 1:
            return True
        if node[1] == state.selection_pixel_size[1] - 1:
            return True
        return False


    for low_node in tqdm.tqdm(state.low_nodes, desc='Processing low nodes'):
        if low_node not in state.graph:
            continue

        lake_height = get_height_by_key(low_node, state)
        for neighbour in state.graph[low_node]:
            if get_height_by_key(neighbour, state) < lake_height:
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

            new_location = get_node_centerpoint(node)
            if node_height < lake_height:
                break
            lake_height = node_height
            merging_nodes.add(node)

            # If node is a border then this means the flow can go off the edge. merging should stop after this node
            if any(does_node_touch_border(i) for i in node):
                break

            for adjacent_node in state.graph[node]:
                if adjacent_node not in nodes_in_queue:
                    new_location = get_node_centerpoint(adjacent_node)
                    nodes_in_queue.add(adjacent_node)
                    heapq.heappush(queue, (get_height_by_key(adjacent_node, state), adjacent_node))

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
                # Merge this
                merging_nodes.add(node)
                new_location = get_node_centerpoint(node)

                for adjacent_node in state.graph[node]:
                    if adjacent_node not in nodes_in_queue:
                        new_location = get_node_centerpoint(adjacent_node)
                        nodes_in_queue.add(adjacent_node)
                        heapq.heappush(queue, (get_height_by_key(adjacent_node, state), adjacent_node))
            else:
                break

        merged_node_key = tuple(sorted({node for node_key in merging_nodes for node in node_key}))
        neighbours = {node for merging_node in merging_nodes for node in state.graph[merging_node]} - set(
            merging_nodes
        )
        for neighbour in neighbours:
            updated_neighbours = set(state.graph[neighbour]) - merging_nodes
            updated_neighbours.add(merged_node_key)
            state.graph[neighbour] = tuple(sorted(updated_neighbours))
        state.graph[merged_node_key] = tuple(sorted(neighbours))
        settings.height_map[merged_node_key[0][1], merged_node_key[0][0]] = lake_height

        for merging_node in merging_nodes:
            del state.graph[merging_node]

    screen.fill((0,0,0))
    print("done")
    yield