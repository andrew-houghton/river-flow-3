from random import randint
from pathlib import Path
import os
import numpy

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from PIL import Image


class GameState:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        size = (infoObject.current_w, infoObject.current_h)

        # self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        self.screen = pygame.display.set_mode(size)
        self.framerate = 165
        self.clock = pygame.time.Clock()

        # Load images
        self.true_colour = self.get_image("true_colour_resized.jpg", size)
        self.height_map = self.get_image("ASTGTMV003_S45E168_dem.png", size)

        # Set startup image
        self.screen.blit(self.true_colour, self.find_centered_image_corner(self.true_colour))
        pygame.display.flip()

        self.running = True
        self.screen_number = 0

    def load_height_map(self, scaled=True):
        im = Image.open(Path(__file__).absolute().parent.parent.joinpath('data').joinpath('ASTGTMV003_S45E168_dem.tif'))
        imarray = numpy.array(im)
        if scaled:
            return (imarray//(imarray.max()/255)).astype('int32')  # // is floor division operator
        else:
            return imarray

    def find_centered_image_corner(self, image):
        screen_center = self.screen.get_rect().center
        image_position = image.get_rect().center
        return (screen_center[0] - image_position[0], screen_center[1] - image_position[1])

    def get_image(self, filename, size=None):
        image = Image.open(Path(__file__).absolute().parent.parent.joinpath("data", filename))
        if size:
            self.scale_ratio = min(size[0] / image.size[0], size[1] / image.size[1])
            self.dem_size = image.size
            new_size = [int(i * self.scale_ratio) for i in image.size]
            image = image.resize(new_size)
        surface = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        return surface

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RIGHT:
                    self.next_screen()

    def main_loop(self):
        while self.running:
            self.handle_events()
            self.clock.tick(self.framerate)

    def next_screen(self):
        self.screen_number += 1
        print(f"Change to screen number {self.screen_number}")

        if self.screen_number == 1:
            fading_out_image = self.true_colour.copy()

            corner = self.find_centered_image_corner(fading_out_image)
            num_steps = 16

            for i in range(num_steps, 0, -1):
                image_alpha = int(255 * i / num_steps)
                fading_out_image.set_alpha(image_alpha)
                self.screen.blit(self.height_map, corner)
                self.screen.blit(fading_out_image, corner)
                pygame.display.flip()
                self.clock.tick(self.framerate)
            self.screen.blit(self.height_map, corner)
            pygame.display.flip()
        if self.screen_number == 2:
            self.selection_pixel_size = self.compute_selection_pixel_size()
            left = randint(0, self.dem_size[0] - 1 - self.selection_pixel_size[0])
            right = left + self.selection_pixel_size[0]
            top = randint(0, self.dem_size[1] - 1 - self.selection_pixel_size[1])
            bottom = top + self.selection_pixel_size[1]

            # Todo, pull height data
            # Todo, save selection in good format
            height_map = self.height_map.copy()
            self.points = ((left, top), (right, top), (right, bottom), (left, bottom))
            self.scaled_points = [(int(x * self.scale_ratio), int(y * self.scale_ratio)) for x, y in self.points]
            green_colour = (0, 204, 51)
            line_width = 3
            pygame.draw.polygon(height_map, green_colour, self.scaled_points, line_width)
            self.screen.blit(height_map, self.find_centered_image_corner(height_map))
            pygame.display.flip()
        if self.screen_number == 3:
            # Get the section of the image
            # Scale up the section step by step
            original_res_height_map = self.get_image("ASTGTMV003_S45E168_dem.png")
            selected_surface = original_res_height_map.subsurface(
                pygame.Rect(
                    self.points[0][0],
                    self.points[0][1],
                    self.points[2][0] - self.points[0][0],
                    self.points[2][1] - self.points[0][1],
                )
            )
            screen_size = self.screen.get_rect().size
            map_corner = self.find_centered_image_corner(self.height_map)
            num_steps = 200
            for i in range(num_steps + 1):
                # Smoothly transition the scale of the selected surface to cover the whole screen
                # TODO: change this section so that it looks like a flat surface moving closer to an observer
                proportion_finished = (i / num_steps) ** 4
                proportion_unfinished = 1 - proportion_finished

                width = (
                    self.selection_pixel_size[0] * self.scale_ratio * proportion_unfinished
                    + screen_size[0] * proportion_finished
                )
                height = (
                    self.selection_pixel_size[1] * self.scale_ratio * proportion_unfinished
                    + screen_size[1] * proportion_finished
                )

                left = int((map_corner[0] + self.scaled_points[0][0]) * proportion_unfinished)
                top = int((map_corner[1] + self.scaled_points[0][1]) * proportion_unfinished)

                self.resized_selected_surface = pygame.transform.scale(selected_surface, (int(width), int(height)))
                self.screen.blit(self.resized_selected_surface, (left, top))
                pygame.display.flip()
        if self.screen_number == 4:
            # Create circles
            circles_surface = pygame.Surface(self.screen.get_rect().size, pygame.SRCALPHA, 32)
            circles_surface = circles_surface.convert_alpha()
            self.draw_circles(circles_surface, self.selection_pixel_size)

            # Remove background image
            num_steps = 30
            resized_selected_surface = self.resized_selected_surface.copy()
            for i in range(num_steps, 0, -1):
                image_alpha = int(255 * i / num_steps)
                resized_selected_surface.set_alpha(image_alpha)
                self.screen.fill((0, 0, 0))
                self.screen.blit(circles_surface, (0, 0))
                self.screen.blit(resized_selected_surface, (0, 0))
                pygame.display.flip()
                self.clock.tick(self.framerate)

    def compute_selection_pixel_size(self, max_pixels=100):
        # Wide dimension of the screen is max_pixels
        # Other dimension of the screen is the same scale
        screen_size = self.screen.get_rect().size
        pixel_size = max(screen_size) / max_pixels
        return int(screen_size[0] / pixel_size), int(screen_size[1] / pixel_size)

    def draw_circles(self, surface, dimensions):
        screen_size = self.screen.get_rect().size
        float_pixel_size = (screen_size[0] / dimensions[0], screen_size[1] / dimensions[1])
        center_offset = (float_pixel_size[0] / 2, float_pixel_size[1] / 2)
        circle_radius = int(max(*float_pixel_size) * 0.35)
        height_array =  self.load_height_map()

        for x in range(dimensions[0]):
            for y in range(dimensions[1]):
                colour = height_array[self.points[0][1]+y, self.points[0][0]+x]
                pygame.draw.circle(
                    surface,
                    (colour, colour, colour),
                    (int(x * float_pixel_size[0] + center_offset[0]), int(y * float_pixel_size[1] + center_offset[1])),
                    circle_radius,
                )


if __name__ == "__main__":
    game = GameState()
    game.main_loop()
