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
    animate_flow,
)
from line_profiler import LineProfiler


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

        self.animation_generators = [
            starting_image,
            true_colour_to_height_map,
            display_selection_polygon,
            scale_up_selection,
            add_circles,
            add_edges,
            merge_equal_height_nodes,
            highlight_low_nodes,
            flood_points,
            animate_flow,
        ]

        # lp = LineProfiler()
        # self.animations = [lp(gen)(screen, self.state, self.settings) for gen in self.animation_generators]
        self.animations = [gen(screen, self.state, self.settings) for gen in self.animation_generators]
        self.main_loop()
        # lp.print_stats()

    def main_loop(self):
        frame_generator = self.next_animation()
        while self.state.running:
            if self.state.within_transition:
                try:
                    update_rect = next(frame_generator)
                    if update_rect:
                        pygame.display.update(pygame.Rect(update_rect))
                    else:
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.state.click_location_1 = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
                self.state.click_location_2 = pygame.mouse.get_pos()


if __name__ == "__main__":
    VisRenderer()
