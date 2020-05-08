import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from vis_dataclasses import VisState, VisSettings
from animations import (
    starting_image,
    true_colour_to_height_map,
    random_selection_polygon,
    scale_up_selection,
    add_circles,
    add_edges,
    merge_equal_height_nodes,
    highlight_low_nodes,
    flood_points,
    animate_watershed,
    animate_flow,
    animate_continous_flow,
)
from line_profiler import LineProfiler
from actions import show_selection_polygon


class VisRenderer:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        # self.settings = VisSettings(screen_size=(infoObject.current_w // 2, infoObject.current_h // 2))
        self.settings = VisSettings(screen_size=(infoObject.current_w, infoObject.current_h))
        self.state = VisState(running=True, within_transition=True)

        self.screen = pygame.display.set_mode(self.settings.screen_size, pygame.FULLSCREEN)
        # screen = pygame.display.set_mode(self.settings.screen_size)
        self.clock = pygame.time.Clock()

        self.animation_generators = [
            (starting_image, None),
            (true_colour_to_height_map, show_selection_polygon),
            (random_selection_polygon, None),
            (scale_up_selection, None),
            (add_circles, None),
            (add_edges, None),
            (merge_equal_height_nodes, None),
            (highlight_low_nodes, None),
            (flood_points, None),
            # (animate_watershed, None),
            # (animate_flow, None),
            (animate_continous_flow, None),
        ]

        # lp = LineProfiler()
        # self.animations = [lp(gen)(screen, self.state, self.settings) for gen in self.animation_generators]
        self.animations = [(gen(self.screen, self.state, self.settings), action_processor) for gen, action_processor in self.animation_generators]
        self.main_loop()
        # lp.print_stats()

    def main_loop(self):
        frame_generator, action_processor = self.next_animation()
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
                frame_generator, action_processor = self.handle_events(action_processor)
                if frame_generator:
                    self.state.within_transition = True

    def next_animation(self):
        try:
            return self.animations.pop(0)
        except IndexError:
            self.state.running = False

    def handle_events(self, action_processor=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and not self.state.within_transition:
                return self.next_animation()
            elif action_processor is not None:
                return action_processor(event, self.screen, self.state, self.settings), action_processor
        return None, action_processor

if __name__ == "__main__":
    VisRenderer()
