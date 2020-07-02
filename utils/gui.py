import sys
import pygame
from pygame import gfxdraw


class GUI:
    def __init__(self, width, height):
        pygame.init()
        self.size = self.width, self.height = width, height
        GUI.screen = pygame.display.set_mode(self.size)

        GUI.clock = pygame.time.Clock()
        GUI.hitcircles = []
        GUI.cursor = Cursor((0, 0), [0, 0])

    def draw(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        self.screen.fill((0, 0, 0))

        for i in GUI.hitcircles:
            i.display()

        GUI.cursor.display()

        pygame.display.flip()


class Hitcircle(GUI):
    def __init__(self, x, y, radius=50, color=(255, 0, 0)):
        self.x = int(x)
        self.y = int(y)
        self.radius = int(radius)
        GUI.hitcircles.append(self)

    def set_position(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def set_color(self, color):
        self.color = color

    def cleanup(self):
        GUI.hitcircles.remove(self)
        del self

    def display(self):
        gfxdraw.aacircle(GUI.screen, self.x, self.y, self.radius, self.color)
        gfxdraw.filled_circle(GUI.screen, self.x, self.y,
                              self.radius, self.color)


class Cursor(GUI):
    def __init__(self, position: tuple, trail_points: list = []):
        self.x = int(position[0])
        self.y = int(position[1])
        self.trail_points = trail_points
        GUI.cursor = self

    def set_cursor_position(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def set_trail_points(self, trail_points):
        self.trail_points = trail_points

    def display(self):
        pygame.draw.circle(GUI.screen, (0, 255, 255),
                           (self.x, self.y), 5, 2)
        if len(self.trail_points) > 1:
            pygame.draw.aalines(GUI.screen, (0, 0, 255),
                                False, self.trail_points)
