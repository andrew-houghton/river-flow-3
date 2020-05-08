import pygame
from vis_dataclasses import VisState, VisSettings
from animations import _compute_selection_pixel_size
from typing import Generator


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
