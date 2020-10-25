import pygame

def show_selection_polygon(event, screen, state, settings):
    if event.type == pygame.MOUSEBUTTONDOWN:
        state.click_location = pygame.mouse.get_pos()

        state.scaled_location = (
            int((state.click_location[0] - state.resized_image_position[0]) / settings.scale_ratio),
            int((state.click_location[1] - state.resized_image_position[1]) / settings.scale_ratio),
        )
        # TODO move click location into image
        # TODO move center inwards if required
        # TODO calculate and store top left spot

        assert state.scaled_location[0] + settings.screen_size[0] <= settings.full_size_dimensions[0]
        assert state.scaled_location[1] + settings.screen_size[1] <= settings.full_size_dimensions[1]

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
        rectangle_bounds = ((left, top), (right, top), (right, bottom), (left, bottom))

        screen.fill((0,0,0))
        screen.blit(settings.pygame_colour_image, state.resized_image_position)
        pygame.draw.polygon(
            screen,
            settings.selection_line_colour,
            rectangle_bounds,
            settings.selection_line_width,
        )
        yield
