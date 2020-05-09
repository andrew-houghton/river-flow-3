import pygame
from vis_dataclasses import VisState, VisSettings
from animations import _compute_selection_pixel_size, _draw_line, get_node_centerpoint
from typing import Generator
from PIL import Image
from algorithms import calculate_watershed, calculate_flow, calculate_continuous_flow
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


def animate_watershed(event, screen, state: VisState, settings: VisSettings) -> Generator:
    if event.type != pygame.MOUSEBUTTONDOWN:
        return

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
        colour = [i * 255 for i in cm.ocean(math.log(flow) / maximum_flow)[:3]]
        pygame.draw.circle(screen, colour, circle_center, radius)

        if i % update_frequency == 0:
            yield
    yield


def animate_flow(event, screen, state: VisState, settings: VisSettings) -> Generator:
    if event.type != pygame.MOUSEBUTTONDOWN:
        return

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
                circle_center = [
                    int(new_location[i] * state.float_pixel_size[i] + state.center_offset[i]) for i in (0, 1)
                ]
                colour = [i * 255 for i in cm.ocean(flow / maximum_flow)[:3]]
                pygame.draw.circle(circles_surface, colour, circle_center, circle_radius)
                circle_drawn = True

        screen.blit(pygame_img, (0, 0))
        screen.blit(edges_surface, (0, 0))
        screen.blit(circles_surface, (0, 0))
        yield

        if not circle_drawn:
            break


def animate_continous_flow(event, screen, state: VisState, settings: VisSettings) -> Generator:
    if event.type != pygame.MOUSEBUTTONDOWN:
        return

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

    node_flows = list(i.copy() for i in calculate_continuous_flow(state, 200))

    for flows in node_flows:
        maximum_flow = math.log(max(flows.values()))
        circles_surface = pygame.Surface(settings.screen_size, pygame.SRCALPHA, 32).convert_alpha()
        circle_drawn = False
        for node, flow in flows.items():
            if flow != 0:
                new_location = get_node_centerpoint(node)
                circle_center = [
                    int(new_location[i] * state.float_pixel_size[i] + state.center_offset[i]) for i in (0, 1)
                ]
                colour = [i * 255 for i in cm.ocean(math.log(flow) / maximum_flow)[:3]]
                pygame.draw.circle(circles_surface, colour, circle_center, circle_radius)
                circle_drawn = True

        screen.blit(pygame_img, (0, 0))
        screen.blit(edges_surface, (0, 0))
        screen.blit(circles_surface, (0, 0))
        yield

        if not circle_drawn:
            break
