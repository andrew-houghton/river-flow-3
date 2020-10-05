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
    show_only_heights,
)
from line_profiler import LineProfiler
from actions import show_selection_polygon, animate_watershed, animate_flow


class VisRenderer:
    def __init__(self):
        pygame.init()
        infoObject = pygame.display.Info()
        self.current_animation_index = -1
        # self.settings = VisSettings(screen_size=(infoObject.current_w // 2, infoObject.current_h // 2))
        self.settings = VisSettings(screen_size=(infoObject.current_w, infoObject.current_h))
        self.state = VisState(running=True, within_transition=True)

        self.render_surface = pygame.display.set_mode(self.settings.screen_size, pygame.FULLSCREEN)
        # self.render_surface = pygame.display.set_mode(self.settings.screen_size)
        self.screen = self.render_surface.copy()
        self.clock = pygame.time.Clock()

        self.animations = [
            (starting_image, None, "New Zealand", None),
            (true_colour_to_height_map, show_selection_polygon, "Height map", "Click two corners to select an area"),
            (random_selection_polygon, None, "Height map", None),
            (scale_up_selection, None, "Selected area of height map", None),
            (add_circles, None, "Height as points", "Each circle represents a physical point, colour indicates height"),
            (add_edges, None, "Point graph", "Water can flow between points, this flow is represented by lines"),
            (merge_equal_height_nodes, None, "Merge equal height points", "If multiple points next to each other are the same height they are merged"),
            (highlight_low_nodes, None, "Low points", "Points below all adjacent points will flood if water is added"),
            (flood_points, None, "Flooding", "Flood these points until there is a direction for water to flow out and down"),
            (show_only_heights, animate_watershed, "Animation: Watershed", "Click somewhere"),
            (show_only_heights, animate_flow, "Animation: Flow", "Click somewhere"),
        ]

        pygame.font.init()
        self.title_font = pygame.font.SysFont('tahoma', 48)
        self.subtitle_font = pygame.font.SysFont('tahoma', 32)
        self.title_text = None
        self.subtitle_text = None
        self.main_loop()

    def main_loop(self):
        frame_generator, action_processor = self.next_animation()
        while self.state.running:
            if self.state.within_transition:
                try:
                    next(frame_generator)
                    self.render_surface.blit(self.screen, (0, 0))
                    self.render_surface.blit(self.text_surface, (0, 0))
                    pygame.display.flip()
                    self.clock.tick(self.settings.framerate)
                    self.handle_events()
                except StopIteration:
                    self.state.within_transition = False
            else:
                frame_generator, action_processor = self.handle_events(action_processor)
                if frame_generator:
                    self.state.within_transition = True

    def update_text(self):
        title_string = self.animations[self.current_animation_index][2] 
        subtitle_string = self.animations[self.current_animation_index][3]
        self.title_text = self.title_font.render(title_string, False, (255, 255, 255))
        if subtitle_string is not None:
            self.subtitle_text = self.subtitle_font.render(subtitle_string, False, (255, 255, 255))
        else:
            self.subtitle_text = None

        self.text_surface = pygame.Surface(self.settings.screen_size, pygame.SRCALPHA, 32)
        self.text_surface = self.text_surface.convert_alpha()
        self.text_surface.blit(self.title_text, (0,0))
        if self.subtitle_text:
            self.text_surface.blit(self.subtitle_text, (0,40))

    def next_animation(self):
        self.current_animation_index += 1
        self.update_text()
        generator = self.animations[self.current_animation_index][0](self.screen, self.state, self.settings)
        return generator, self.animations[self.current_animation_index][1]

    def previous_animation(self):
        if self.current_animation_index == 0:
            return None, None
        self.current_animation_index -= 1
        self.update_text()
        generator = self.animations[self.current_animation_index][0](self.screen, self.state, self.settings)
        return generator, self.animations[self.current_animation_index][1]

    def handle_events(self, action_processor=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and not self.state.within_transition:
                if self.current_animation_index == len(self.animations) - 1:
                    return None, action_processor
                return self.next_animation()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT and not self.state.within_transition:
                return self.previous_animation()
            elif action_processor is not None:
                return action_processor(event, self.screen, self.state, self.settings), action_processor
        return None, action_processor

if __name__ == "__main__":
    VisRenderer()
