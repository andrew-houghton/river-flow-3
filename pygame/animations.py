from vis_dataclasses import VisState, VisSettings
from typing import Generator
from random import randint
import pygame
from matplotlib import cm
from pprint import pprint


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


def compute_selection_pixel_size(screen_size, max_pixels):
    # Wide dimension of the screen is max_pixels
    # Other dimension of the screen is the same scale
    pixel_size = max(screen_size) / max_pixels
    return int(screen_size[0] / pixel_size), int(screen_size[1] / pixel_size)


def display_selection_polygon(screen, state: VisState, settings: VisSettings) -> Generator:
    # TODO: Only show polygon within screen

    state.selection_pixel_size = compute_selection_pixel_size(settings.screen_size, settings.max_pixels)

    shown_screen_dimensions = [int(i / settings.scale_ratio) for i in settings.screen_size]
    left = randint(0, shown_screen_dimensions[0] - 1 - state.selection_pixel_size[0])
    right = left + state.selection_pixel_size[0]
    top = randint(0, shown_screen_dimensions[1] - 1 - state.selection_pixel_size[1])
    bottom = top + state.selection_pixel_size[1]

    state.points = ((left, top), (right, top), (right, bottom), (left, bottom))
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


def _draw_circles(screen_size, height_array, surface, dimensions, points, skipped_coordinates=None):
    skipped_coordinates = skipped_coordinates or []
    float_pixel_size = (screen_size[0] / dimensions[0], screen_size[1] / dimensions[1])
    center_offset = (float_pixel_size[0] / 2, float_pixel_size[1] / 2)
    circle_radius = int(max(*float_pixel_size) * 0.35)
    height_array = (height_array // (height_array.max() / 255)).astype("int32")

    for x in range(dimensions[0]):
        for y in range(dimensions[1]):
            if (x, y) not in skipped_coordinates:
                height = height_array[points[0][1] + y, points[0][0] + x]
                colour = [i * 255 for i in cm.viridis(height / 255)[:3]]
                pygame.draw.circle(
                    surface,
                    colour,
                    (int(x * float_pixel_size[0] + center_offset[0]), int(y * float_pixel_size[1] + center_offset[1])),
                    circle_radius,
                )


def add_circles(screen, state: VisState, settings: VisSettings) -> Generator:

    state.circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
    _draw_circles(
        settings.screen_size, settings.height_map, state.circles_surface, state.selection_pixel_size, state.points
    )

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


def add_edges(screen, state: VisState, settings: VisSettings) -> Generator:

    float_pixel_size = (
        settings.screen_size[0] / state.selection_pixel_size[0],
        settings.screen_size[1] / state.selection_pixel_size[1],
    )
    center_offset = (float_pixel_size[0] / 2, float_pixel_size[1] / 2)
    screen.fill((0, 0, 0))
    for i in range(sum(state.selection_pixel_size)):
        for j in range(i):
            # Horizontal lines
            if i - j < state.selection_pixel_size[0]:
                pygame.draw.line(
                    screen,
                    (255, 255, 255),
                    (
                        int((i - j - 1) * float_pixel_size[0] + center_offset[0]),
                        int(j * float_pixel_size[1] + center_offset[1]),
                    ),
                    (
                        int((i - j) * float_pixel_size[0] + center_offset[0]),
                        int(j * float_pixel_size[1] + center_offset[1]),
                    ),
                    2,
                )
            # Vertical lines
            if i - j < state.selection_pixel_size[1]:
                pygame.draw.line(
                    screen,
                    (255, 255, 255),
                    (
                        int(j * float_pixel_size[0] + center_offset[0]),
                        int((i - j - 1) * float_pixel_size[1] + center_offset[1]),
                    ),
                    (
                        int(j * float_pixel_size[0] + center_offset[0]),
                        int((i - j) * float_pixel_size[1] + center_offset[1]),
                    ),
                    2,
                )
        screen.blit(state.circles_surface, (0, 0))
        yield


def merge_equal_height_nodes(screen, state: VisState, settings: VisSettings) -> Generator:
    # 1. Loop through all pixels
    # 2. DFS to any adjancent nodes of equal height
    # 3. Store co-ordinates of points to be merged

    # create a surface with the circles which don't move
    # for every point which moved calculate it's start and end position
    # then render frames 1 by one by redrawing all the circles which move, and the connections to those points

    def get_adjacent_equal_height_nodes(x, y, height):
        nodes = set()
        if x > 0 and height == settings.height_map[state.points[0][1] + y, state.points[0][0] + x - 1]:
            nodes.add((x - 1, y))
        if (
            x < state.selection_pixel_size[0] - 1
            and height == settings.height_map[state.points[0][1] + y, state.points[0][0] + x + 1]
        ):
            nodes.add((x + 1, y))
        if y > 0 and height == settings.height_map[state.points[0][1] + y - 1, state.points[0][0] + x]:
            nodes.add((x, y - 1))
        if (
            y < state.selection_pixel_size[1] - 1
            and height == settings.height_map[state.points[0][1] + y + 1, state.points[0][0] + x]
        ):
            nodes.add((x, y + 1))
        return nodes

    node_merge_operations = []
    skip_nodes = set()

    for x in range(state.selection_pixel_size[0]):
        for y in range(state.selection_pixel_size[1]):
            if (x, y) not in skip_nodes:
                height = settings.height_map[state.points[0][1] + y, state.points[0][0] + x]

                visited, queue = set(), [(x, y)]
                while queue:
                    vertex = queue.pop(0)
                    if vertex not in visited:
                        visited.add(vertex)
                        queue.extend(get_adjacent_equal_height_nodes(*vertex, height) - visited - skip_nodes)

                if visited != {(x, y)}:
                    node_merge_operations.append(visited)
                    for node in visited:
                        skip_nodes.add(node)

    state.circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()

    float_pixel_size = (
        settings.screen_size[0] / state.selection_pixel_size[0],
        settings.screen_size[1] / state.selection_pixel_size[1],
    )
    center_offset = (float_pixel_size[0] / 2, float_pixel_size[1] / 2)
    # Draw all the lines between nodes which are not changing
    def draw_line(surface, from_node, to_node):
        pygame.draw.line(
            surface,
            (255, 255, 255),
            (
                int(from_node[0] * float_pixel_size[0] + center_offset[0]),
                int(from_node[1] * float_pixel_size[1] + center_offset[1]),
            ),
            (
                int(to_node[0] * float_pixel_size[0] + center_offset[0]),
                int(to_node[1] * float_pixel_size[1] + center_offset[1]),
            ),
            2,
        )

    non_skip_nodes = [
        (x, y)
        for x in range(state.selection_pixel_size[0])
        for y in range(state.selection_pixel_size[1])
        if (x, y) not in skip_nodes
    ]
    for from_node in non_skip_nodes:
        for to_node in non_skip_nodes:
            if from_node > to_node:
                if (abs(from_node[0] - to_node[0]) == 1 and from_node[1] == to_node[1]) or (
                    abs(from_node[1] - to_node[1]) == 1 and from_node[0] == to_node[0]
                ):
                    draw_line(state.circles_surface, from_node, to_node)

    _draw_circles(
        settings.screen_size,
        settings.height_map,
        state.circles_surface,
        state.selection_pixel_size,
        state.points,
        skip_nodes,
    )

    node_movements = {}
    for merging_nodes in node_merge_operations:
        new_location = (
            sum(x for x, y in merging_nodes) / len(merging_nodes),
            sum(y for x, y in merging_nodes) / len(merging_nodes),
        )
        for node in merging_nodes:
            node_movements[node] = new_location

    num_steps = 50
    circle_radius = int(max(*float_pixel_size) * 0.35)
    height_array = (settings.height_map // (settings.height_map.max() / 255)).astype("int32")

    def get_adjacent_nodes(x, y):
        nodes = set()
        if x > 0:
            nodes.add((x - 1, y))
        if x < state.selection_pixel_size[0] - 1:
            nodes.add((x + 1, y))
        if y > 0:
            nodes.add((x, y - 1))
        if y < state.selection_pixel_size[1] - 1:
            nodes.add((x, y + 1))
        return nodes

    def get_updated_node_position(node, new_position, progress):
        x = node[0] + i / num_steps * (new_position[0] - node[0])
        y = node[1] + i / num_steps * (new_position[1] - node[1])
        return x, y

    for i in range(1, num_steps + 1):
        screen.fill((0, 0, 0))
        moving_circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()

        for node, new_position in node_movements.items():
            adjacent_nodes = [j for j in get_adjacent_nodes(*node) if j not in skip_nodes or j < node]
            for adjacent_node in adjacent_nodes:
                if adjacent_node in skip_nodes:
                    adjacent_node_position = get_updated_node_position(
                        adjacent_node, node_movements[adjacent_node], i / num_steps
                    )
                else:
                    adjacent_node_position = adjacent_node
                draw_line(
                    moving_circles_surface,
                    get_updated_node_position(node, new_position, i / num_steps),
                    adjacent_node_position,
                )

        for node, new_position in node_movements.items():
            current_x, current_y = get_updated_node_position(node, new_position, i / num_steps)
            height = height_array[state.points[0][1] + node[1], state.points[0][0] + node[0]]
            colour = [i * 255 for i in cm.viridis(height / 255)[:3]]
            pygame.draw.circle(
                moving_circles_surface,
                colour,
                (
                    int(current_x * float_pixel_size[0] + center_offset[0]),
                    int(current_y * float_pixel_size[1] + center_offset[1]),
                ),
                circle_radius,
            )
        screen.blit(moving_circles_surface, (0, 0))
        screen.blit(state.circles_surface, (0, 0))
        yield
