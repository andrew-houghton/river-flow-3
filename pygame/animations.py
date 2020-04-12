from vis_dataclasses import VisState, VisSettings
from typing import Generator
from random import randint
import pygame
from matplotlib import cm
from pprint import pprint
from algorithms import equal_height_node_merge, create_graph, find_low_nodes
import heapq


def starting_image(screen, state: VisState, settings: VisSettings) -> Generator:
    screen.blit(settings.screen_size_true_colour, (0, 0))
    yield


def true_colour_to_height_map(screen, state: VisState, settings: VisSettings) -> Generator:
    num_steps = 10
    fading_out_image = settings.screen_size_true_colour.copy()

    for i in range(num_steps, 0, -1):
        image_alpha = int(255 * i / num_steps)
        fading_out_image.set_alpha(image_alpha)
        screen.blit(settings.screen_size_height_image, (0, 0))
        screen.blit(fading_out_image, (0, 0))
        yield

    screen.blit(settings.screen_size_height_image, (0, 0))
    yield


def _compute_selection_pixel_size(screen_size, max_pixels):
    # Wide dimension of the screen is max_pixels
    # Other dimension of the screen is the same scale
    pixel_size = max(screen_size) / max_pixels
    return int(screen_size[0] / pixel_size), int(screen_size[1] / pixel_size)


def display_selection_polygon(screen, state: VisState, settings: VisSettings) -> Generator:
    state.selection_pixel_size = _compute_selection_pixel_size(settings.screen_size, settings.max_pixels)
    state.float_pixel_size = (
        settings.screen_size[0] / state.selection_pixel_size[0],
        settings.screen_size[1] / state.selection_pixel_size[1],
    )
    state.center_offset = (state.float_pixel_size[0] / 2, state.float_pixel_size[1] / 2)

    shown_screen_dimensions = [int(i / settings.scale_ratio) for i in settings.screen_size]

    num_tries = 0
    highest_point_altitude = 0
    while num_tries < 10 and highest_point_altitude <= 0:
        left = randint(0, shown_screen_dimensions[0] - 1 - state.selection_pixel_size[0])
        right = left + state.selection_pixel_size[0]
        top = randint(0, shown_screen_dimensions[1] - 1 - state.selection_pixel_size[1])
        bottom = top + state.selection_pixel_size[1]
        state.points = ((left, top), (right, top), (right, bottom), (left, bottom))
        state.selected_area_height_map = settings.height_map[
            state.points[0][1] : state.points[0][1] + state.selection_pixel_size[1],
            state.points[0][0] : state.points[0][0] + state.selection_pixel_size[0],
        ]
        highest_point_altitude = state.selected_area_height_map.max()

    state.scaled_points = [(int(x * settings.scale_ratio), int(y * settings.scale_ratio)) for x, y in state.points]
    pygame.draw.polygon(
        settings.screen_size_height_image,
        settings.selection_line_colour,
        state.scaled_points,
        settings.selection_line_width,
    )
    screen.blit(settings.screen_size_height_image, (0, 0))
    yield


def scale_up_selection(screen, state: VisState, settings: VisSettings) -> Generator:
    # Get the section of the image
    # Scale up the section step by step
    selected_surface = settings.full_size_height_image.subsurface(
        pygame.Rect(
            state.points[0][0],
            state.points[0][1],
            state.points[2][0] - state.points[0][0],
            state.points[2][1] - state.points[0][1],
        )
    )

    num_steps = 10

    for i in range(num_steps + 1):
        # Smoothly transition the scale of the selected surface to cover the whole screen
        # TODO: change this section so that it looks like a flat surface moving closer to an observer
        proportion_finished = (i / num_steps) ** 3
        proportion_unfinished = 1 - proportion_finished

        width = int(
            state.selection_pixel_size[0] * settings.scale_ratio * proportion_unfinished
            + settings.screen_size[0] * proportion_finished
        )
        height = int(
            state.selection_pixel_size[1] * settings.scale_ratio * proportion_unfinished
            + settings.screen_size[1] * proportion_finished
        )

        left = int(state.scaled_points[0][0] * proportion_unfinished)
        top = int(state.scaled_points[0][1] * proportion_unfinished)

        state.resized_selected_surface = pygame.transform.scale(selected_surface, (width, height))
        screen.blit(state.resized_selected_surface, (left, top))
        yield


def _draw_circles(surface, state, settings, skipped_coordinates=None, absolute_scale=True):
    skipped_coordinates = skipped_coordinates or []
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    if absolute_scale:
        height_array = (settings.height_map // (settings.height_map.max() / 255)).astype("int32")
    else:
        height_array = state.selected_area_height_map - state.selected_area_height_map.min()
        height_array = (height_array // (height_array.max() / 255)).astype("int32")

    for x in range(state.selection_pixel_size[0]):
        for y in range(state.selection_pixel_size[1]):
            if (x, y) not in skipped_coordinates:
                if absolute_scale:
                    height = height_array[state.points[0][1] + y, state.points[0][0] + x]
                else:
                    height = height_array[y, x]
                colour = [i * 255 for i in cm.gist_earth(height / 255)[:3]]
                pygame.draw.circle(
                    surface,
                    colour,
                    (
                        int(x * state.float_pixel_size[0] + state.center_offset[0]),
                        int(y * state.float_pixel_size[1] + state.center_offset[1]),
                    ),
                    circle_radius,
                )


def add_circles(screen, state: VisState, settings: VisSettings) -> Generator:
    state.circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
    _draw_circles(state.circles_surface, state, settings)

    # Remove background image
    num_steps = 10
    state.resized_selected_surface = state.resized_selected_surface.convert()
    for i in range(num_steps, -1, -1):
        image_alpha = int(255 * i / num_steps)
        state.resized_selected_surface.set_alpha(image_alpha)
        screen.fill((0, 0, 0))
        screen.blit(state.resized_selected_surface, (0, 0))
        screen.blit(state.circles_surface, (0, 0))
        yield


def _get_adjacent_nodes(node, state, filter_function=lambda *args: True):
    x, y = node
    nodes = set()
    if x > 0:
        nodes.add((x - 1, y))
    if x < state.selection_pixel_size[0] - 1:
        nodes.add((x + 1, y))
    if y > 0:
        nodes.add((x, y - 1))
    if y < state.selection_pixel_size[1] - 1:
        nodes.add((x, y + 1))
    return [i for i in nodes if filter_function((x, y), i)]


# TODO Reuse this function above
def _draw_line(surface, from_node, to_node, state):
    pygame.draw.line(
        surface,
        (255, 255, 255),
        (
            int(from_node[0] * state.float_pixel_size[0] + state.center_offset[0]),
            int(from_node[1] * state.float_pixel_size[1] + state.center_offset[1]),
        ),
        (
            int(to_node[0] * state.float_pixel_size[0] + state.center_offset[0]),
            int(to_node[1] * state.float_pixel_size[1] + state.center_offset[1]),
        ),
        2,
    )


def add_edges(screen, state: VisState, settings: VisSettings) -> Generator:
    height_array = state.selected_area_height_map - state.selected_area_height_map.min()
    height_array = (height_array // (height_array.max() / 255)).astype("int32")
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    for x in range(state.selection_pixel_size[0]):
        for y in range(state.selection_pixel_size[1]):
            if x > 0:
                _draw_line(screen, (x, y), (x - 1, y), state)
            if y > 0:
                _draw_line(screen, (x, y), (x, y - 1), state)

        if x > 0:
            for y in range(state.selection_pixel_size[1]):
                colour = [i * 255 for i in cm.gist_earth(height_array[y, x] / 255)[:3]]
                pygame.draw.circle(
                    screen,
                    colour,
                    (
                        int((x - 1) * state.float_pixel_size[0] + state.center_offset[0]),
                        int(y * state.float_pixel_size[1] + state.center_offset[1]),
                    ),
                    circle_radius,
                )
                pygame.draw.circle(
                    screen,
                    colour,
                    (
                        int(x * state.float_pixel_size[0] + state.center_offset[0]),
                        int(y * state.float_pixel_size[1] + state.center_offset[1]),
                    ),
                    circle_radius,
                )
        yield


def merge_equal_height_nodes(screen, state: VisState, settings: VisSettings) -> Generator:
    # 1. Loop through all pixels
    # 2. DFS to any adjancent nodes of equal height
    # 3. Store co-ordinates of points to be merged
    # create a surface with the circles which don't move
    # for every point which moved calculate it's start and end position
    # then render frames 1 by one by redrawing all the circles which move, and the connections to those points

    node_movements, skip_nodes, node_merge_operations = equal_height_node_merge(state, settings)
    state.circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
    non_skip_nodes = [
        (x, y)
        for x in range(state.selection_pixel_size[0])
        for y in range(state.selection_pixel_size[1])
        if (x, y) not in skip_nodes
    ]
    state.graph = create_graph(node_merge_operations, skip_nodes, non_skip_nodes, state)
    for from_node in non_skip_nodes:
        for to_node in non_skip_nodes:
            if from_node > to_node:
                if (abs(from_node[0] - to_node[0]) == 1 and from_node[1] == to_node[1]) or (
                    abs(from_node[1] - to_node[1]) == 1 and from_node[0] == to_node[0]
                ):
                    _draw_line(state.circles_surface, from_node, to_node, state)

    _draw_circles(state.circles_surface, state, settings, skip_nodes, absolute_scale=False)

    num_steps = 50
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    height_array = state.selected_area_height_map - state.selected_area_height_map.min()
    height_array = (height_array // (height_array.max() / 255)).astype("int32")

    def get_updated_node_position(node, new_position, progress):
        x = node[0] + i / num_steps * (new_position[0] - node[0])
        y = node[1] + i / num_steps * (new_position[1] - node[1])
        return x, y

    for i in range(1, num_steps + 1):
        screen.fill((0, 0, 0))
        moving_circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()

        for node, new_position in node_movements.items():
            adjacent_nodes = _get_adjacent_nodes(node, state, lambda x, y: x < y or x in skip_nodes)
            for adjacent_node in adjacent_nodes:
                if adjacent_node in skip_nodes:
                    adjacent_node_position = get_updated_node_position(
                        adjacent_node, node_movements[adjacent_node], i / num_steps
                    )
                else:
                    adjacent_node_position = adjacent_node
                _draw_line(
                    moving_circles_surface,
                    get_updated_node_position(node, new_position, i / num_steps),
                    adjacent_node_position,
                    state,
                )

        for node, new_position in node_movements.items():
            current_x, current_y = get_updated_node_position(node, new_position, i / num_steps)
            colour = [i * 255 for i in cm.gist_earth(height_array[node[1], node[0]] / 255)[:3]]
            pygame.draw.circle(
                moving_circles_surface,
                colour,
                (
                    int(current_x * state.float_pixel_size[0] + state.center_offset[0]),
                    int(current_y * state.float_pixel_size[1] + state.center_offset[1]),
                ),
                circle_radius,
            )

        screen.blit(moving_circles_surface, (0, 0))
        screen.blit(state.circles_surface, (0, 0))
        yield


def get_height_by_key(key, state):
    return state.selected_area_height_map[key[0][1], key[0][0]]


def highlight_low_nodes(screen, state: VisState, settings: VisSettings) -> Generator:
    circle_radius = int(max(*state.float_pixel_size) * 0.37)

    state.low_nodes = find_low_nodes(state.graph, state)
    print(f"Found {len(state.low_nodes)} low nodes")

    for low_node in state.low_nodes:
        new_location = (sum(x for x, y in low_node) / len(low_node), sum(y for x, y in low_node) / len(low_node))
        pygame.draw.circle(
            screen,
            (255, 0, 0),
            (
                int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
            ),
            circle_radius,
            3,
        )
    state.low_nodes = sorted(state.low_nodes, key=lambda key: get_height_by_key(key, state))
    yield


def flood_points(screen, state: VisState, settings: VisSettings) -> Generator:
    """
    Highlight all the neighbours (and add them to a priority queue).

    Loop through the priority queue;
        Check if the node is lower than the lake
        Merge the node with the lake
        Add the other neighbours to the priority queue
    """

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

    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    if not state.low_nodes:
        yield

    low_node = state.low_nodes[0]
    lake_height = get_height_by_key(low_node, state)
    queue = [(lake_height, low_node)]
    nodes_in_queue = {low_node}

    while True:
        try:
            node_height, node = heapq.heappop(queue)
        except IndexError:
            print("heap ran out of items but it shouldn't")
            break

        print(f"Moved to next node {node}")
        print(f"Adjacent nodes are {state.graph[node]}")

        new_location = (sum(x for x, y in node) / len(node), sum(y for x, y in node) / len(node))
        if node_height < lake_height:
            print("Exited because we found an outflow route")
            pygame.draw.circle(
                screen,
                (0, 255, 0),
                (
                    int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                    int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
                ),
                circle_radius,
                3,
            )
            break

        lake_height = node_height
        pygame.draw.circle(
            screen,
            (255, 0, 0),
            (
                int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
            ),
            circle_radius,
            3,
        )
        yield

        # If node is a border then this means the flow can go off the edge. merging should stop after this node
        if any(does_node_touch_border(i) for i in node):
            print("Existed because we reached border")
            pygame.draw.circle(
                screen,
                (0, 255, 0),
                (
                    int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                    int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
                ),
                circle_radius,
                3,
            )
            break

        for adjacent_node in state.graph[node]:
            if adjacent_node not in nodes_in_queue:
                print(f"Adding adjacent node {adjacent_node}")
                new_location = (
                    sum(x for x, y in adjacent_node) / len(adjacent_node),
                    sum(y for x, y in adjacent_node) / len(adjacent_node),
                )
                pygame.draw.circle(
                    screen,
                    (255, 165, 0),
                    (
                        int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                        int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
                    ),
                    circle_radius,
                    3,
                )
                nodes_in_queue.add(adjacent_node)
                heapq.heappush(queue, (get_height_by_key(adjacent_node, state), adjacent_node))
            else:
                print(f"Skipped {adjacent_node} because already visited")
        yield
    yield
