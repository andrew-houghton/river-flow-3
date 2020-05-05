from vis_dataclasses import VisState, VisSettings
from typing import Generator
from random import randint
import pygame
from matplotlib import cm
from pprint import pprint
from algorithms import equal_height_node_merge, create_graph, find_low_nodes, calculate_watershed, calculate_flow
import heapq
from functools import lru_cache
from collections import defaultdict
import math
import numpy
from PIL import Image


@lru_cache(maxsize=10000)
def get_node_centerpoint(node):
    return (sum(x for x, _ in node) / len(node), sum(y for _, y in node) / len(node))


@lru_cache(maxsize=4000)
def get_colour_by_height(height):
    return [i * 255 for i in cm.gist_earth(height / 255)[:3]]


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
    shown_screen_dimensions = [int(i / settings.scale_ratio) for i in settings.screen_size]

    if state.click_location_1 and state.click_location_2:
        scaled_location_1 = (
            int(state.click_location_1[0] / settings.scale_ratio),
            int(state.click_location_1[1] / settings.scale_ratio),
        )
        scaled_location_2 = (
            int(state.click_location_2[0] / settings.scale_ratio),
            int(state.click_location_2[1] / settings.scale_ratio),
        )

        left = min(scaled_location_1[0], scaled_location_2[0])
        right = max(scaled_location_1[0], scaled_location_2[0])
        top = min(scaled_location_1[1], scaled_location_2[1])
        bottom = max(scaled_location_1[1], scaled_location_2[1])

        screen_fill_ratio_x = (right - left) / shown_screen_dimensions[0]
        screen_fill_ratio_y = (bottom - top) / shown_screen_dimensions[1]
        screen_fill_ratio = min(screen_fill_ratio_x, screen_fill_ratio_y)
        if screen_fill_ratio_x < screen_fill_ratio_y:
            bottom = top + screen_fill_ratio_x * shown_screen_dimensions[1]
        else:
            right = left + screen_fill_ratio_y * shown_screen_dimensions[0]

        state.selection_pixel_size = _compute_selection_pixel_size(
            settings.screen_size, max(right - left, bottom - top)
        )
        state.points = ((left, top), (right, top), (right, bottom), (left, bottom))
        state.selected_area_height_map = settings.height_map[
            state.points[0][1] : state.points[0][1] + state.selection_pixel_size[1],
            state.points[0][0] : state.points[0][0] + state.selection_pixel_size[0],
        ]
    else:
        state.selection_pixel_size = _compute_selection_pixel_size(settings.screen_size, settings.max_pixels)
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
    state.float_pixel_size = (
        settings.screen_size[0] / state.selection_pixel_size[0],
        settings.screen_size[1] / state.selection_pixel_size[1],
    )
    state.center_offset = (state.float_pixel_size[0] / 2, state.float_pixel_size[1] / 2)

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


def _draw_circles(surface, state, settings, skipped_coordinates=None, absolute_scale=True, set_colour=None):
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
                colour = set_colour or get_colour_by_height(height)
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
        1,
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
                colour = get_colour_by_height(height_array[y, x])
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

    non_skip_nodes_set = set(non_skip_nodes)
    for from_node in non_skip_nodes_set:
        if (from_node[0] + 1, from_node[1]) in non_skip_nodes_set:
            _draw_line(state.circles_surface, from_node, (from_node[0] + 1, from_node[1]), state)
        if (from_node[0], from_node[1] + 1) in non_skip_nodes_set:
            _draw_line(state.circles_surface, from_node, (from_node[0], from_node[1] + 1), state)

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
            colour = get_colour_by_height(height_array[node[1], node[0]])
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
        new_location = get_node_centerpoint(low_node)
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

    for low_node in state.low_nodes:
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
            merging_nodes.add(node)

            # If node is a border then this means the flow can go off the edge. merging should stop after this node
            if any(does_node_touch_border(i) for i in node):
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

            for adjacent_node in state.graph[node]:
                if adjacent_node not in nodes_in_queue:
                    new_location = get_node_centerpoint(adjacent_node)
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
            yield

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

                for adjacent_node in state.graph[node]:
                    if adjacent_node not in nodes_in_queue:
                        new_location = get_node_centerpoint(adjacent_node)
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
                yield
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
        state.selected_area_height_map[merged_node_key[0][1], merged_node_key[0][0]] = lake_height

        # Find all the nodes don't touch the merged area
        untouched_nodes = state.graph.keys() - {merged_node_key} - set(merging_nodes)
        untouched_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()

        height_array = state.selected_area_height_map - state.selected_area_height_map.min()
        height_array = (height_array // (height_array.max() / 255)).astype("int32")

        for node in untouched_nodes:
            new_location = get_node_centerpoint(node)
            for neighbour in state.graph[node]:
                if neighbour < node:
                    neighbour_location = get_node_centerpoint(neighbour)
                    _draw_line(untouched_surface, new_location, neighbour_location, state)

        for node in untouched_nodes:
            new_location = get_node_centerpoint(node)
            height = height_array[node[0][1], node[0][0]]
            colour = get_colour_by_height(height)
            pygame.draw.circle(
                untouched_surface,
                colour,
                (
                    int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                    int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
                ),
                circle_radius,
            )
            if node in state.low_nodes:
                pygame.draw.circle(
                    untouched_surface,
                    (255, 0, 0),
                    (
                        int(new_location[0] * state.float_pixel_size[0] + state.center_offset[0]),
                        int(new_location[1] * state.float_pixel_size[1] + state.center_offset[1]),
                    ),
                    circle_radius,
                    3,
                )

        num_steps = 10
        new_location = get_node_centerpoint(merged_node_key)
        for i in range(1, num_steps + 1):
            screen.fill((0, 0, 0))
            screen.blit(untouched_surface, (0, 0))
            for original_node in merging_nodes:
                original_node_position = (
                    sum(x for x, y in original_node) / len(original_node),
                    sum(y for x, y in original_node) / len(original_node),
                )
                actual_node_position = (
                    (new_location[0] - original_node_position[0]) * i / num_steps + original_node_position[0],
                    (new_location[1] - original_node_position[1]) * i / num_steps + original_node_position[1],
                )
                for neighbour in state.graph[original_node]:
                    if neighbour not in merging_nodes:
                        neighbour_position = get_node_centerpoint(neighbour)
                        # Move edge from to position
                        _draw_line(screen, neighbour_position, actual_node_position, state)

                        height = height_array[neighbour[0][1], neighbour[0][0]]
                        colour = get_colour_by_height(height)
                        pygame.draw.circle(
                            screen,
                            colour,
                            (
                                int(neighbour_position[0] * state.float_pixel_size[0] + state.center_offset[0]),
                                int(neighbour_position[1] * state.float_pixel_size[1] + state.center_offset[1]),
                            ),
                            circle_radius,
                        )

                height = height_array[original_node[0][1], original_node[0][0]]
                colour = get_colour_by_height(height)
                pygame.draw.circle(
                    screen,
                    colour,
                    (
                        int(actual_node_position[0] * state.float_pixel_size[0] + state.center_offset[0]),
                        int(actual_node_position[1] * state.float_pixel_size[1] + state.center_offset[1]),
                    ),
                    circle_radius,
                )
            yield

        for merging_node in merging_nodes:
            del state.graph[merging_node]


def animate_watershed(screen, state: VisState, settings: VisSettings) -> Generator:
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    height_array = state.selected_area_height_map - state.selected_area_height_map.min()
    height_array = (height_array // (height_array.max() / 255)).astype("int32")
    image = Image.fromarray(numpy.uint8(cm.gist_earth(height_array) * 255))
    pygame_img = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
    pygame_img = pygame.transform.scale(
        pygame_img, [int(pygame_img.get_rect().size[i] * state.float_pixel_size[i]) for i in (0, 1)]
    )

    screen.blit(pygame_img, (0, 0))

    state.node_flows, state.edge_flows = calculate_watershed(state)
    state.node_flow_items = list(state.node_flows.items())
    node_flow_indexes = {state.node_flow_items[i][0]: i for i in range(len(state.node_flow_items))}

    maximum_flow = math.log(max(state.node_flow_items, key=lambda x: x[1])[1])

    num_steps = 200
    update_frequency = int(len(state.node_flows) / num_steps)

    for i in range(len(state.node_flow_items)):
        node, flow = state.node_flow_items[i]
        new_location = get_node_centerpoint(node)

        for neighbour in state.graph[node]:
            if node_flow_indexes[neighbour] > i:
                neighbour_location = get_node_centerpoint(neighbour)
                _draw_line(screen, new_location, neighbour_location, state)

        circle_center = [int(new_location[i] * state.float_pixel_size[i] + state.center_offset[i]) for i in (0, 1)]
        radius = int(circle_radius * max(1, math.log(flow) / 3))
        colour = [i * 255 for i in cm.gist_heat(math.log(flow) / maximum_flow)[:3]]
        pygame.draw.circle(screen, colour, circle_center, radius)

        if i % update_frequency == 0:
            yield
    yield

def animate_flow(screen, state: VisState, settings: VisSettings) -> Generator:
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    height_array = state.selected_area_height_map - state.selected_area_height_map.min()
    height_array = (height_array // (height_array.max() / 255)).astype("int32")
    image = Image.fromarray(numpy.uint8(cm.gist_earth(height_array) * 255))
    pygame_img = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
    pygame_img = pygame.transform.scale(
        pygame_img, [int(pygame_img.get_rect().size[i] * state.float_pixel_size[i]) for i in (0, 1)]
    )
    screen.blit(pygame_img, (0, 0))
    yield

    edges_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
    for node in state.graph:
        new_location = get_node_centerpoint(node)
        for neighbour in state.graph[node]:
            if neighbour > node:
                neighbour_location = get_node_centerpoint(neighbour)
                _draw_line(edges_surface, new_location, neighbour_location, state)

    node_flows = list(i.copy() for i in calculate_flow(state, 200))

    for flows in node_flows:
        maximum_flow = max(flows.values())
        circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
        circle_drawn = False
        for node, flow in flows.items():
            if flow != 0:
                new_location = get_node_centerpoint(node)
                circle_center = [int(new_location[i] * state.float_pixel_size[i] + state.center_offset[i]) for i in (0, 1)]
                colour = [i * 255 for i in cm.ocean(flow / maximum_flow)[:3]]
                pygame.draw.circle(circles_surface, colour, circle_center, circle_radius)
                circle_drawn = True

        screen.blit(pygame_img, (0 , 0))
        screen.blit(edges_surface, (0 , 0))
        screen.blit(circles_surface, (0 , 0))
        yield

        if not circle_drawn:
            break