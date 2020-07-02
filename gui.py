import sys
import pygame


class GUI:
    def __init__(self, width, height):
        pygame.init()
        self.size = self.width, self.height = width, height
        GUI.screen = pygame.display.set_mode(self.size)

        GUI.hitcircles = []

    def draw(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            self.screen.fill((0, 0, 0))
            for i in GUI.hitcircles:
                i.display()
            pygame.display.flip()


class Hitcircle(GUI):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        GUI.hitcircles.append(self)

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def cleanup(self):
        GUI.hitcircles.remove(self)
        del self

    def display(self):
        pygame.draw.circle(GUI.screen, (255, 0, 0),
                           (self.x, self.y), 50, 2)


"""
Example:

// main:
    gui = GUI(512, 384)
    hc = Hitcircle(50,60)
    hc2 = Hitcircle(150, 100)
    while 1:
        gui.draw()
"""
