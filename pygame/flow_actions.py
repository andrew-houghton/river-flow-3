import pygame
import numpy
from matplotlib import cm
from algorithms import calculate_watershed
from flow_dataclasses import write_colour_to_screen
from tqdm import tqdm


def show_selection_polygon(event, screen, state, settings):
    if event.type == pygame.MOUSEBUTTONDOWN:
        state.click_location = pygame.mouse.get_pos()


        # First find size of rectangle (Should be screen size 1:1)
        rectangle_size = (
            int(settings.scale_ratio * settings.screen_size[0]),
            int(settings.scale_ratio * settings.screen_size[1])
        )

        # Then move the click location in towards the center of the rectangle
        width_from_side_to_center = state.resized_image_position[0] + rectangle_size[0]/2
        rectangle_x = max(width_from_side_to_center, state.click_location[0])
        rectangle_x = min(rectangle_x, settings.screen_size[0] - width_from_side_to_center)
        rectangle_x = int(rectangle_x)
        height_from_top_to_center = state.resized_image_position[1]+rectangle_size[1]/2
        rectangle_y = max(height_from_top_to_center, state.click_location[1])
        rectangle_y = min(rectangle_y, settings.screen_size[1] - height_from_top_to_center)
        rectangle_y = int(rectangle_y)

        # Then calculate the bounds of the rectangle
        left = rectangle_x - rectangle_size[0] // 2
        right = rectangle_x + rectangle_size[0] // 2
        top = rectangle_y - rectangle_size[1] // 2
        bottom = rectangle_y + rectangle_size[1] // 2
        state.rectangle_bounds = ((left, top), (right, top), (right, bottom), (left, bottom))

        # Adjust click location to top left of bounding box
        adjusted_click_location = (
            state.click_location[0] - rectangle_size[0]//2,
            state.click_location[1] - rectangle_size[1]//2,
        )

        # Find co-ordinates of click
        state.scaled_location = (
            int((adjusted_click_location[0] - state.resized_image_position[0]) / settings.scale_ratio),
            int((adjusted_click_location[1] - state.resized_image_position[1]) / settings.scale_ratio),
        )
        # Move click to be the top left of a valid screen size rectangle
        state.scaled_location = (
            max(min(state.scaled_location[0], settings.full_size_dimensions[0] - settings.screen_size[0] - 1), 0),
            max(min(state.scaled_location[1], settings.full_size_dimensions[1] - settings.screen_size[1] - 1), 0),
        )

        assert state.scaled_location[0] + settings.screen_size[0] <= settings.full_size_dimensions[0]
        assert state.scaled_location[1] + settings.screen_size[1] <= settings.full_size_dimensions[1]

        screen.fill((0,0,0))
        screen.blit(settings.pygame_colour_image, state.resized_image_position)
        pygame.draw.polygon(
            screen,
            settings.selection_line_colour,
            state.rectangle_bounds,
            settings.selection_line_width,
        )
        yield


def animate_watershed(event, screen, state, settings):
    if event.type == pygame.MOUSEBUTTONDOWN:
        source = (pygame.mouse.get_pos(),)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        source = None
    else:
        return

    screen.fill((0,0,0))

    state.node_flows, _ = calculate_watershed(state, source=source)
    state.node_flow_items = list(state.node_flows.items())
    numpy_image = numpy.zeros((settings.screen_size[1], settings.screen_size[0], 3), dtype=numpy.uint8)

    print(f"Num pixels to process {len(state.node_flow_items)}")

    for i in tqdm(range(len(state.node_flow_items)), desc="processing pixels"):
        node, flow = state.node_flow_items[i]
        colour = [int(i * 255) for i in cm.gist_heat(flow)[:3]]
        # print(node)
        # print(flow)
        # print(colour)
        for point in node:
            numpy_image[point[1], point[0]] = colour
        if i%20 == 0:
            # print("Updating screen")
            write_colour_to_screen(screen, numpy_image)
            yield

    write_colour_to_screen(screen, numpy_image)
    yield
