import sys
import pygame
from pygame import gfxdraw


class GUI:
    def __init__(self, width, height):
        pygame.init()
        self.size = self.width, self.height = width, height
        GUI.screen = pygame.display.set_mode(self.size)

        GUI.mouse = pygame.mouse.get_pos()
        GUI.click = pygame.mouse.get_pressed()

        GUI.clock = pygame.time.Clock()
        GUI.hitcircles = []
        GUI.buttons = []
        GUI.cursor = Cursor((0, 0), [0, 0])

    def draw(self):
        GUI.mouse = pygame.mouse.get_pos()
        GUI.click = pygame.mouse.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        self.screen.fill((0, 0, 0))

        for i in GUI.hitcircles:
            i.display()

        for i in GUI.buttons:
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


class Button(GUI):
    def __init__(self, x, y, width, height, text, on_click=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.on_click = on_click

        self.font = pygame.font.Font("freesansbold.ttf", 15)
        self.is_holding_down = False

        GUI.buttons.append(self)

    def set_text(self, text):
        self.text = text

    def display(self):
        if(self.x+self.width > GUI.mouse[0] > self.x and self.y+self.height > GUI.mouse[1] > self.y):
            pygame.draw.rect(GUI.screen, (220, 220, 220),
                             (self.x, self.y, self.width, self.height))
            if GUI.click[0] == 1:
                if not self.is_holding_down:
                    if self.on_click != None:
                        self.on_click()
                        self.is_holding_down = True
            else:
                self.is_holding_down = False
        else:
            pygame.draw.rect(GUI.screen, (255, 255, 255),
                             (self.x, self.y, self.width, self.height))

        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = ((self.x+(self.width/2)),
                            (self.y+(self.height/2)))
        GUI.screen.blit(text_surface, text_rect)
