import sys
import pygame
from pygame import gfxdraw
from utils.mathhelper import clamp, is_inside_radius
from utils.curves import Bezier


class GUI:
    def __init__(self, width, height, offset_x=0, offset_y=0):
        pygame.init()
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.size = self.width, self.height = width + 2 * offset_x, height + 2 * offset_y
        GUI.screen = pygame.display.set_mode(self.size)
        GUI.play_area = pygame.Surface((width, height))

        GUI.mouse = pygame.mouse.get_pos()
        GUI.click = pygame.mouse.get_pressed()
        GUI.keys = pygame.key.get_pressed()

        GUI.clock = pygame.time.Clock()
        GUI.hitcircles = []
        GUI.elements = []
        GUI.cursor = Cursor((0, 0))

        GUI.is_holding_down_key = [0] * len(GUI.keys)
        GUI.is_single_press_key = [0] * len(GUI.keys)

        GUI.is_holding_down = False
        GUI.is_single_click = False

        GUI.single_press_events = []
        GUI.holding_down_events = []

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

    def keyboard_events(self):
        GUI.keys = pygame.key.get_pressed()
        for i in range(len(GUI.keys)):
            if GUI.keys[i]:
                if not GUI.is_holding_down_key[i]:
                    GUI.is_single_press_key[i] = True
                    GUI.is_holding_down_key[i] = True
                else:
                    GUI.is_single_press_key[i] = False
            else:
                GUI.is_single_press_key[i] = False
                GUI.is_holding_down_key[i] = False

    def handle_key_events(self):
        for keys, event in GUI.single_press_events:
            for key in keys:
                if not GUI.is_single_press_key[key]:
                    break
            else:
                event()

        for keys, event in GUI.holding_down_events:
            for key in keys:
                if not GUI.is_holding_down_key[key]:
                    break
            else:
                event()

    def add_single_press_event(self, keys, event):
        GUI.single_press_events.append((keys, event))

    def add_holding_down_event(self, keys, event):
        GUI.holding_down_events.append((keys, event))

    def draw(self):
        self.mouse_events()
        self.keyboard_events()

        self.handle_key_events()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        self.screen.fill((20, 20, 20))
        self.play_area.fill((0, 0, 0))

        for i in GUI.hitcircles:
            i.display()

        GUI.cursor.display()

        GUI.screen.blit(GUI.play_area, (self.offset_x, self.offset_y))

        for i in GUI.elements:
            i.display()

        pygame.display.flip()


class OSU(GUI):
    def __init__(self, current_frame, is_hardrock=False):
        OSU.current_frame = current_frame
        OSU.is_hardrock = is_hardrock

    def set_current_frame(self, current_frame):
        OSU.current_frame = current_frame


class Hitcircle(OSU):
    def __init__(self, x, y, time, radius=50, color=(255, 0, 0)):
        self.x = int(x)
        self.y = int(y)
        self.radius = int(radius)
        self.time = time
        self.color = color

        osu_width, osu_height = (512, 384)
        play_area_width, play_area_height = GUI.play_area.get_size()
        self.offset_width, self.offset_height = (
            (play_area_width - osu_width) // 2, (play_area_height - osu_height) // 2)

        GUI.hitcircles.append(self)

    def set_position(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def set_color(self, color):
        self.color = color

    def cleanup(self):
        GUI.hitcircles.remove(self)
        del self

    def set_time(self, i):
        self.time = i

    def set_current_time(self, i):
        self.current_time = i

    def display(self):
        if not (0 < (self.time - OSU.current_frame.time) < 450):
            return

        if is_inside_radius(
                (OSU.current_frame.x, OSU.current_frame.y), (self.x, self.y),
                self.radius):
            self.set_color((0, 255, 0))
        else:
            self.set_color((255, 0, 0))

        # Approach circle
        for i in range(2):  # <---- line width
            gfxdraw.aacircle(
                GUI.play_area,
                self.x + self.offset_width,
                self.y + self.offset_height,
                self.radius + i +
                int(min((self.time - OSU.current_frame.time) / 5, 90)),
                (255, 255, 255))

        # Hit Circle
        gfxdraw.aacircle(
            GUI.play_area,
            self.x + self.offset_width,
            self.y + self.offset_height,
            self.radius,
            self.color)
        gfxdraw.filled_circle(GUI.play_area, self.x + self.offset_width, self.y + self.offset_height,
                              self.radius, self.color)
        gfxdraw.aacircle(
            GUI.play_area,
            self.x + self.offset_width,
            self.y + self.offset_height,
            2,
            (255, 255, 255))


class Hitobject_Slider(OSU):
    def __init__(self, control_points, circle_radius, time, duration,
                 show_control_points=False, color=(255, 0, 0)):
        self.control_points = control_points
        self.bezier = Bezier(control_points)
        self.circle_radius = circle_radius
        self.color = color
        self.time = time
        self.duration = duration
        self.show_control_points = show_control_points
        GUI.hitcircles.append(self)
        self.n = 0

    def set_control_points(self, control_points):
        self.bezier = Bezier(control_points)

    def display(self):
        if not (0 - self.duration < (self.time - OSU.current_frame.time) < 450):
            return

        play_area_width, play_area_height = GUI.play_area.get_size()
        # offset between play area and GUI surface
        self.offset_width = (play_area_width - 512) // 2
        # offset between play area and GUI surface
        self.offset_height = (play_area_height - 384) // 2

        for i in [self.bezier.pos[0], self.bezier.pos[len(
                self.bezier.pos) // 2], self.bezier.pos[-1]]:
            a = i
            gfxdraw.aacircle(
                GUI.play_area,
                int(a.x) + self.offset_width,
                int(a.y) + self.offset_height,
                int(self.circle_radius),
                (0, 0, 255))
        l1 = []
        l2 = []
        for i in range(1, len(self.bezier.pos), 10):
            diffx = self.bezier.pos[i].x - self.bezier.pos[i - 1].x
            diffy = self.bezier.pos[i].y - self.bezier.pos[i - 1].y
            slope = diffy / diffx
            b = pow(pow(self.circle_radius, 2) / (pow(slope, 2) + 1), 0.5)
            a = -slope * b
            l1.append(
                (self.bezier.pos[i].x +
                 a +
                 self.offset_width,
                 self.bezier.pos[i].y +
                 b + self.offset_height))
            l2.append(
                (self.bezier.pos[i].x -
                 a +
                 self.offset_width,
                 self.bezier.pos[i].y -
                 b + self.offset_height))

        pygame.draw.aalines(
            GUI.play_area,
            pygame.Color("cyan"),
            False,
            l1,
            3)

        pygame.draw.aalines(GUI.play_area, pygame.Color("gray"), False, [
            (i.x + self.offset_width, i.y + self.offset_height) for i in self.bezier.pos], 3)

        pygame.draw.aalines(
            GUI.play_area,
            pygame.Color("cyan"),
            False,
            l2,
            3)
        if self.show_control_points:
            for i in self.control_points:
                pygame.draw.circle(GUI.play_area, (255, 0, 0),
                                   (i.x, i.y), 5, 1)


class Cursor(GUI):
    def __init__(self, position: tuple, trail_points: list = [],
                 path_points: list = [], show_path=False, show_markers=True):
        self.x = int(position[0])
        self.y = int(position[1])
        self.trail_points = trail_points
        self.path_points = path_points
        self.show_path = show_path
        self.show_markers = show_markers

        play_area_width, play_area_height = GUI.play_area.get_size()
        # offset between play area and GUI surface
        self.offset_width = (play_area_width - 512) // 2
        # offset between play area and GUI surface
        self.offset_height = (play_area_height - 384) // 2

        GUI.cursor = self

    def toggle_show_markers(self):
        self.show_markers = not self.show_markers

    def set_cursor_position(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def set_trail_points(self, trail_points):
        self.trail_points = [
            (point[0] + self.offset_width,
             point[1] + self.offset_height) for point in trail_points]

    def set_path_points(self, path_points):
        self.path_points = [
            (point[0] + self.offset_width,
             point[1] + self.offset_height) for point in path_points]

    def display(self):
        pygame.draw.circle(GUI.play_area, (0, 255, 255),
                           (self.x + self.offset_width, self.y + self.offset_height), 5, 2)
        if len(self.trail_points) > 1:
            pygame.draw.aalines(GUI.play_area, (0, 0, 255),
                                False, self.trail_points)
        if len(self.path_points) > 1 and self.show_path:
            pygame.draw.aalines(GUI.play_area, (255, 0, 255),
                                False, self.path_points)

        if self.show_markers:
            for i in self.trail_points:
                a = 3
                pygame.draw.line(GUI.play_area, (255, 255, 0),
                                 (i[0] + a, i[1] + a), (i[0] - a, i[1] - a))

                pygame.draw.line(GUI.play_area, (255, 255, 0),
                                 (i[0] - a, i[1] + a), (i[0] + a, i[1] - a))

            for i in self.path_points:
                a = 3
                pygame.draw.line(GUI.play_area, (255, 255, 255),
                                 (i[0] + a, i[1] + a), (i[0] - a, i[1] - a))

                pygame.draw.line(GUI.play_area, (255, 255, 255),
                                 (i[0] - a, i[1] + a), (i[0] + a, i[1] - a))


class Button(GUI):
    def __init__(self, x, y, width, height, text, on_click=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.on_click = on_click

        self.font = pygame.font.Font("NotoSans-Black.ttf", 15)

        GUI.elements.append(self)

    def set_text(self, text):
        self.text = text

    def display(self):
        if (self.x + self.width >
                GUI.mouse[0] > self.x and self.y + self.height > GUI.mouse[1] > self.y):
            pygame.draw.rect(GUI.screen, (220, 220, 220),
                             (self.x, self.y, self.width, self.height))
            if GUI.is_single_click and self.on_click is not None:
                self.on_click()
        else:
            pygame.draw.rect(GUI.screen, (255, 255, 255),
                             (self.x, self.y, self.width, self.height))

        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = ((self.x + (self.width / 2)),
                            (self.y + (self.height / 2)))
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

        self.is_dragging_ball = False
        self.is_setting_value = False
        GUI.elements.append(self)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def check_mouse_on_ball(self, x, y):
        diff = pow(x - GUI.mouse[0], 2) + pow(y - GUI.mouse[1], 2)
        return (pow(diff, 0.5) < 7)

    def check_mouse_on_slider(self):
        if self.x + self.width * \
                2 > GUI.mouse[0] > self.x and self.y + self.height * 2 > GUI.mouse[1] > self.y:
            return True
        else:
            return False

    def display(self):
        circle_origin_x = self.x + \
            int(self.width * (self.value / self.max_value))
        circle_origin_y = self.y + int(self.height / 2)

        pygame.draw.rect(GUI.screen, (255, 255, 255),
                         (self.x, self.y, self.width, self.height))

        if self.check_mouse_on_ball(circle_origin_x, circle_origin_y):
            if GUI.is_single_click:
                self.is_dragging_ball = True
                self.drag_origin_x = GUI.mouse[0]
                self.drag_origin_y = GUI.mouse[1]
        if self.is_dragging_ball and GUI.is_holding_down:
            circle_origin_x = GUI.mouse[0]
            circle_origin_x = clamp(
                circle_origin_x, self.x, self.x + self.width)
            self.value = (circle_origin_x - self.x) * \
                self.max_value / self.width
        else:
            self.is_dragging_ball = False
            if self.check_mouse_on_slider():
                if GUI.is_single_click:
                    circle_origin_x = GUI.mouse[0]
                    circle_origin_x = clamp(
                        circle_origin_x, self.x, self.x + self.width)
                    self.value = (circle_origin_x - self.x) * \
                        self.max_value / self.width
                    self.is_dragging_ball = True

        ball_size = 8 if self.is_dragging_ball else 7

        gfxdraw.aacircle(GUI.screen, circle_origin_x,
                         circle_origin_y, ball_size, (0, 255, 255))
        gfxdraw.filled_circle(GUI.screen, circle_origin_x,
                              circle_origin_y, ball_size, (0, 255, 255))
        gfxdraw.aacircle(GUI.screen, circle_origin_x,
                         circle_origin_y, ball_size - 2, (0, 0, 0))
        if self.is_dragging_ball:
            gfxdraw.filled_circle(GUI.screen, circle_origin_x,
                                  circle_origin_y, ball_size - 2, (0, 0, 0))


class TextBox(GUI):
    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

        self.font_size = 10
        self.font = pygame.font.Font("NotoSans-Black.ttf", self.font_size)
        GUI.elements.append(self)

    def set_text(self, text):
        self.text = text

    def clear(self):
        self.text = ""

    def display(self):
        label = self.font.render(self.text, True, (255, 255, 255))
        rect = label.get_rect()
        rect.center = ((self.x + (self.width / 2)),
                       (self.y) + (self.height / 2))
        GUI.screen.blit(label, rect)


class DebugBox(GUI):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.texts = []
        self.font_size = 10
        self.font = pygame.font.Font("NotoSans-Black.ttf", self.font_size)
        GUI.elements.append(self)

    def add_text(self, text):
        self.texts.append(text)

    def clear(self):
        self.texts = []

    def display(self):
        labels = []
        label_rects = []
        pygame.draw.rect(GUI.screen, (255, 255, 255),
                         (self.x, self.y, self.width, self.height), 1)
        for index, text in enumerate(self.texts):
            tmp_label = self.font.render(text, True, (255, 255, 255))
            tmp_rect = tmp_label.get_rect()
            tmp_rect.center = ((self.x + (self.width / 2)),
                               (self.y) + 10 + (index * self.font_size))

            labels.append(tmp_label)
            label_rects.append(tmp_rect)
        for i in range(len(labels)):
            GUI.screen.blit(labels[i], label_rects[i])
