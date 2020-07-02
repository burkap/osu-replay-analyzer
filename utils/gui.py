import sys
import pygame
from pygame import gfxdraw
from utils.mathhelper import clamp

class GUI:
    def __init__(self, width, height):
        pygame.init()
        self.size = self.width, self.height = width, height
        GUI.screen = pygame.display.set_mode(self.size)

        GUI.mouse = pygame.mouse.get_pos()
        GUI.click = pygame.mouse.get_pressed()

        GUI.clock = pygame.time.Clock()
        GUI.hitcircles = []
        GUI.elements = []
        GUI.cursor = Cursor((0, 0))
        GUI.is_holding_down = False
        GUI.is_single_click = False

    def mouse_events(self):
        GUI.mouse = pygame.mouse.get_pos()
        GUI.click = pygame.mouse.get_pressed()

        if GUI.click[0] == 1:
            if not GUI.is_holding_down:
                GUI.is_single_click = True
                GUI.is_holding_down = True
            else:
                GUI.is_single_click = False
        else:
            GUI.is_single_click = False
            GUI.is_holding_down = False

    def draw(self):
        self.mouse_events()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        self.screen.fill((0, 0, 0))

        for i in GUI.hitcircles:
            i.display()

        for i in GUI.elements:
            i.display()
        GUI.cursor.display()

        pygame.display.flip()


class Hitcircle(GUI):
    def __init__(self, x, y, radius=50, color=(255, 0, 0)):
        self.x = int(x)
        self.y = int(y)
        self.radius = int(radius)
        self.color = color
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

        GUI.elements.append(self)

    def set_text(self, text):
        self.text = text

    def display(self):
        if(self.x+self.width > GUI.mouse[0] > self.x and self.y+self.height > GUI.mouse[1] > self.y):
            pygame.draw.rect(GUI.screen, (220, 220, 220),
                             (self.x, self.y, self.width, self.height))
            if GUI.is_single_click and self.on_click != None:
                self.on_click()
        else:
            pygame.draw.rect(GUI.screen, (255, 255, 255),
                             (self.x, self.y, self.width, self.height))

        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = ((self.x+(self.width/2)),
                            (self.y+(self.height/2)))
        GUI.screen.blit(text_surface, text_rect)


class Slider(GUI):
    def __init__(self, x, y, width, height, value, max_value):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = value
        self.max_value = max_value

        self.drag_origin_x = 0
        self.drag_origin_y = 0

        self.is_dragging = False
        GUI.elements.append(self)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def check_mouse_on_ball(self, x, y):
        diff = pow(x-GUI.mouse[0], 2)+pow(y-GUI.mouse[1], 2)
        return (pow(diff, 0.5) < 7)

    def display(self):
        print(self.value)
        circle_origin_x = self.x + int(self.width*(self.value/self.max_value))
        circle_origin_y = self.y + int(self.height/2)

        pygame.draw.rect(GUI.screen, (255, 255, 255),
                         (self.x, self.y, self.width, self.height))

        if self.check_mouse_on_ball(circle_origin_x, circle_origin_y):
            if GUI.is_single_click:
                self.is_dragging = True
                self.drag_origin_x = GUI.mouse[0]
                self.drag_origin_y = GUI.mouse[1]
        if self.is_dragging and GUI.is_holding_down:
            circle_origin_x = GUI.mouse[0]
            circle_origin_x = clamp(circle_origin_x, self.x, self.x+self.width)
            self.value = (circle_origin_x-self.x)*self.max_value/self.width
        else:
            self.is_dragging = False

        gfxdraw.aacircle(GUI.screen, circle_origin_x,
                         circle_origin_y, 7, (0, 255, 255))
        gfxdraw.filled_circle(GUI.screen, circle_origin_x,
                              circle_origin_y, 7, (0, 255, 255))
        gfxdraw.aacircle(GUI.screen, circle_origin_x,
                         circle_origin_y, 5, (0, 0, 0))
        if self.is_dragging:
            gfxdraw.filled_circle(GUI.screen, circle_origin_x,
                                  circle_origin_y, 5, (0, 0, 0))
