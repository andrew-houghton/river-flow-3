import pygame
from vis_dataclasses import VisState, VisSettings
from animations import _compute_selection_pixel_size, _draw_line, get_node_centerpoint
from typing import Generator
from PIL import Image
from algorithms import calculate_watershed, calculate_flow
from matplotlib import cm
import numpy
import math


def show_selection_polygon(event, screen, state: VisState, settings: VisSettings) -> Generator:
    if event.type == pygame.MOUSEBUTTONDOWN:
        state.click_location_1 = pygame.mouse.get_pos()
    elif event.type == pygame.MOUSEBUTTONUP:
        state.click_location_2 = pygame.mouse.get_pos()

        shown_screen_dimensions = [int(i / settings.scale_ratio) for i in settings.screen_size]

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

def manhattan_dist(a, b):
    return sum(abs(i-j) for i, j in zip(a, b))

def find_clicked_node(position, state):
    scaled_location = list((position[i] - state.center_offset[i])/ state.float_pixel_size[i] for i in (0, 1))
    return min(state.graph, key=lambda node: manhattan_dist(get_node_centerpoint(node), scaled_location))

def animate_watershed(event, screen, state: VisState, settings: VisSettings) -> Generator:
    if event.type == pygame.MOUSEBUTTONDOWN:
        source = find_clicked_node(pygame.mouse.get_pos(), state)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        source = None
    else:
        return
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    screen.blit(state.pygame_img, (0, 0))

    state.node_flows, state.edge_flows = calculate_watershed(state, source=source)
    state.node_flow_items = list(state.node_flows.items())
    node_flow_indexes = {state.node_flow_items[i][0]: i for i in range(len(state.node_flow_items))}

    j=0
    for i in range(len(state.node_flow_items)):
        node, flow = state.node_flow_items[i]
        if flow > 0.0001:
            new_location = get_node_centerpoint(node)

            for neighbour in state.graph[node]:
                if neighbour in node_flow_indexes and node_flow_indexes[neighbour] > i:
                    neighbour_location = get_node_centerpoint(neighbour)
                    _draw_line(screen, new_location, neighbour_location, state)

            j += 1
            circle_center = [int(new_location[i] * state.float_pixel_size[i] + state.center_offset[i]) for i in (0, 1)]
            colour = [i * 255 for i in cm.gist_heat(flow)[:3]]
            pygame.draw.circle(screen, colour, circle_center, circle_radius)
            if j%20 == 0:
                yield
    yield


def animate_flow(event, screen, state: VisState, settings: VisSettings) -> Generator:
    if event.type == pygame.MOUSEBUTTONDOWN:
        source = find_clicked_node(pygame.mouse.get_pos(), state)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        source = None
    else:
        return
    circle_radius = int(max(*state.float_pixel_size) * 0.35)
    screen.blit(state.pygame_img, (0, 0))
    yield

    for flows in calculate_flow(state, 200, source=source):
        # Draw edges between nodes
        edges_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
        for node in flows:
            new_location = get_node_centerpoint(node)
            for neighbour in state.graph[node]:
                if neighbour > node and neighbour in flows:
                    neighbour_location = get_node_centerpoint(neighbour)
                    _draw_line(edges_surface, new_location, neighbour_location, state)

        circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
        circle_drawn = False
        for node, flow in flows.items():
            if flow != 0:
                new_location = get_node_centerpoint(node)
                circle_center = [
                    int(new_location[i] * state.float_pixel_size[i] + state.center_offset[i]) for i in (0, 1)
                ]
                colour = [i * 255 for i in cm.gist_heat(flow)[:3]]
                pygame.draw.circle(circles_surface, colour, circle_center, circle_radius)
                circle_drawn = True

        screen.blit(state.pygame_img, (0, 0))
        screen.blit(edges_surface, (0, 0))
        screen.blit(circles_surface, (0, 0))
        yield

        if not circle_drawn:
            break
