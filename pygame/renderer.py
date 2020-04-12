import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from vis_dataclasses import VisState, VisSettings
from animations import (
    starting_image,
    true_colour_to_height_map,
    display_selection_polygon,
    scale_up_selection,
    add_circles,
    add_edges,
    merge_equal_height_nodes,
    highlight_low_nodes,
    flood_points,
)


class VisRenderer:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        # self.settings = VisSettings(screen_size=(infoObject.current_w // 2, infoObject.current_h // 2))
        self.settings = VisSettings(screen_size=(infoObject.current_w, infoObject.current_h))
        self.state = VisState(running=True, within_transition=True)

        screen = pygame.display.set_mode(self.settings.screen_size, pygame.FULLSCREEN)
        # screen = pygame.display.set_mode(self.settings.screen_size)
        self.clock = pygame.time.Clock()

        self.animations = [
            starting_image(screen, self.state, self.settings),
            true_colour_to_height_map(screen, self.state, self.settings),
            display_selection_polygon(screen, self.state, self.settings),
            scale_up_selection(screen, self.state, self.settings),
            add_circles(screen, self.state, self.settings),
            add_edges(screen, self.state, self.settings),
            merge_equal_height_nodes(screen, self.state, self.settings),
            highlight_low_nodes(screen, self.state, self.settings),
            flood_points(screen, self.state, self.settings),
        ]
        self.main_loop()

    def main_loop(self):
        frame_generator = self.next_animation()
        while self.state.running:
            if self.state.within_transition:
                try:
                    next(frame_generator)
                    pygame.display.flip()
                    self.clock.tick(self.settings.framerate)
                    self.handle_events()
                except StopIteration:
                    self.state.within_transition = False
            else:
                frame_generator = self.handle_events()
                if frame_generator:
                    self.state.within_transition = True

    def next_animation(self):
        try:
            return self.animations.pop(0)
        except IndexError:
            self.state.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and not self.state.within_transition:
                return self.next_animation()


if __name__ == "__main__":
    VisRenderer()
