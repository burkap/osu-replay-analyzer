import sys
import pygame
from pygame import gfxdraw


class GUI:
    def __init__(self, width, height):
        pygame.init()
        self.size = self.width, self.height = width, height
        GUI.screen = pygame.display.set_mode(self.size)

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
    def __init__(self, x, y, radius=50):
        self.x = x
        self.y = y
        self.radius = radius
        GUI.hitcircles.append(self)

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def cleanup(self):
        GUI.hitcircles.remove(self)
        del self

    def display(self):
        gfxdraw.aacircle(GUI.screen, self.x, self.y, self.radius, (255, 0, 0))
        gfxdraw.filled_circle(GUI.screen, self.x, self.y,
                              self.radius, (255, 0, 0))


class Cursor(GUI):
    def __init__(self, position: tuple, trail_points: list = []):
        self.x = position[0]
        self.y = position[1]
        self.trail_points = trail_points
        GUI.cursor = self

    def change__trail_points(self, trail_points):
        self.trail_points = trail_points

    def display(self):

        pygame.draw.circle(GUI.screen, (255, 0, 0),
                           (self.x, self.y), 5, 2)
        if len(self.trail_points) > 1:
            pygame.draw.aalines(GUI.screen, (0, 0, 255),
                                False, self.trail_points)


"""
Example:

// main:
    gui = GUI(512, 384)
    hc = Hitcircle(50, 60, 31)
    trail = Cursor((150, 70), [(10, 10), (20, 25), (150, 70)])
    while 1:
        gui.draw()
"""
