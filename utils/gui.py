import sys
import pygame
import mutagen.mp3

from pygame import gfxdraw
from pygame.constants import *
from utils.mathhelper import clamp, is_inside_radius
from utils.curves import Bezier


class GUI:
    cursor = None
    cursor_trail = None

    screen = None
    play_area = None

    mouse = None
    click = None
    keys = None

    clock = None
    hitcircles = []
    elements = []

    is_holding_down_key = None
    is_single_press_key = None

    is_holding_down = False
    is_single_click = False

    single_press_events = []
    holding_down_events = []

    def __init__(self, width, height, offset_x=0, offset_y=0):
        self.song_file = "data/audio.mp3"

        mp3 = mutagen.mp3.MP3(self.song_file)
        self.rate = (mp3.info.sample_rate)
        pygame.mixer.init(
            frequency=self.rate)
        self.volume = 0.3
        pygame.mixer.music.load(self.song_file)
        pygame.mixer.music.set_volume(self.volume)

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

        GUI.is_holding_down_key = [0] * len(GUI.keys)
        GUI.is_single_press_key = [0] * len(GUI.keys)


        self.music_playing = False
        self.last_music_time = 0
        self.last_pos_time = 0

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
        for keys, event, *args in GUI.single_press_events:
            for key in keys:
                if not GUI.is_single_press_key[key]:
                    break
            else:
                event(*args)

        for keys, event, *args in GUI.holding_down_events:
            for key in keys:
                if not GUI.is_holding_down_key[key]:
                    break
            else:
                event(*args)

    def add_single_press_event(self, keys, event, *args):
        GUI.single_press_events.append((keys, event, *args))

    def add_holding_down_event(self, keys, event, *args):
        GUI.holding_down_events.append((keys, event, *args))

    def set_volume(self, n):
        pygame.mixer.music.set_volume(n)

    def change_play_speed(self, n):
        pygame.mixer.quit()
        new_rate = int(self.rate*n)
        pygame.mixer.init(
            frequency=new_rate)
        pygame.mixer.music.load(self.song_file)
        pygame.mixer.music.set_volume(self.volume)
        self.play_music()

    def play_music(self):
        pygame.mixer.music.play()
        self.music_playing = True

    def pause_music(self):
        if self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False

    def unpause_music(self):
        if not self.music_playing:
            pygame.mixer.music.unpause()
            self.music_playing = True

    def get_music_pos(self):
        return pygame.mixer.music.get_pos() - self.last_pos_time + self.last_music_time

    def set_music_pos(self, x):
        pygame.mixer.music.rewind()
        pygame.mixer.music.set_pos(x/1000)
        self.last_music_time = x
        self.last_pos_time = pygame.mixer.music.get_pos()

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

        GUI.cursor_trail.display()
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
    def __init__(self, x, y, time, score, radius=50, color=(255, 0, 0)):
        self.x = int(x)
        self.y = int(y)
        self.score = score
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

    def display(self):
        if not (0 < (self.time - OSU.current_frame.time) < 450):
            return
        if self.score[3] == 300:
            self.set_color((140, 140, 140))
        elif self.score[3] == 100:
            self.set_color((70, 255, 70))
        elif self.score[3] == 50:
            self.set_color((255, 140, 70))
        elif self.score[3] == 0:
            self.set_color((255, 70, 70))

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
                              self.radius, (255, 255, 255))
        gfxdraw.filled_circle(GUI.play_area, self.x + self.offset_width, self.y + self.offset_height,
                              self.radius-4, self.color)
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


class CursorTrail(GUI):

    def __init__(self, trail_points: dict = {},
                 path_points: dict = {},
                 show_markers=True):
        self.trailing_points = trail_points
        self.leading_points = path_points
        self.show_markers = show_markers
        self.show_path = True

        play_area_width, play_area_height = GUI.play_area.get_size()
        # offset between play area and GUI surface
        self.offset_width = (play_area_width - 512) // 2
        # offset between play area and GUI surface
        self.offset_height = (play_area_height - 384) // 2

        GUI.cursor_trail = self

    def toggle_show_markers(self):
        self.show_markers = not self.show_markers

    def toggle_show_path(self):
        self.show_path = not self.show_path

    def set_trailing_points(self, trailing_frames):
        self.trailing_points = [{"pos": [frame.x + self.offset_width,
                                         frame.y + self.offset_height],
                                 "keys": [frame.m1_pressed,
                                          frame.m2_pressed,
                                          frame.k1_pressed,
                                          frame.k2_pressed,
                                          frame.smoke_pressed]} for frame in trailing_frames]

    def set_leading_points(self, leading_points):
        self.leading_points = [{"pos": [frame.x + self.offset_width,
                                        frame.y + self.offset_height],
                                "keys": [frame.m1_pressed,
                                         frame.m2_pressed,
                                         frame.k1_pressed,
                                         frame.k2_pressed,
                                         frame.smoke_pressed]} for frame in leading_points]

    def get_key_color(self, keys):
        color = [216, 216, 216]

        if keys[2]:
            color[1] = 0
        if keys[3]:
            color[2] = 0

        return color

    def display(self):
        if len(self.trailing_points) > 1:
            for frame1, frame2 in zip(self.trailing_points[:-1], self.trailing_points[1:]):
                color = self.get_key_color(frame1["keys"])
                start_pos = frame1["pos"]
                end_pos = frame2["pos"]
                pygame.draw.aaline(GUI.play_area, color, start_pos, end_pos)
        if len(self.leading_points) > 1 and self.show_path:
            for frame1, frame2 in zip(self.leading_points[:-1], self.leading_points[1:]):
                color = self.get_key_color(frame1["keys"])
                start_pos = frame1["pos"]
                end_pos = frame2["pos"]
                pygame.draw.aaline(GUI.play_area, color, start_pos, end_pos)

        if self.show_markers:
            a = 3
            for frame_point in self.trailing_points:
                x, y = frame_point["pos"]
                pygame.draw.line(GUI.play_area, (255, 255, 0),
                                 (x + a, y + a), (x - a, y - a))
                pygame.draw.line(GUI.play_area, (255, 255, 0),
                                 (x - a, y + a), (x + a, y - a))
            for frame_point in self.leading_points:
                x, y = frame_point["pos"]
                pygame.draw.line(GUI.play_area, (255, 255, 255),
                                 (x + a, y + a), (x - a, y - a))
                pygame.draw.line(GUI.play_area, (255, 255, 255),
                                 (x - a, y + a), (x + a, y - a))


class Cursor(GUI):
    def __init__(self, position: tuple):
        self.x = int(position[0])
        self.y = int(position[1])

        play_area_width, play_area_height = GUI.play_area.get_size()
        # offset between play area and GUI surface
        self.offset_width = (play_area_width - 512) // 2
        # offset between play area and GUI surface
        self.offset_height = (play_area_height - 384) // 2

        GUI.cursor = self

    def set_cursor_position(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def display(self):
        pygame.draw.circle(GUI.play_area, (0, 255, 255),
                           (self.x + self.offset_width, self.y + self.offset_height), 5, 2)


class Button(GUI):
    def __init__(self, x, y, width, height, text, on_click, *args):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.on_click = on_click
        self.args = args

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
                self.on_click(*self.args)
        else:
            pygame.draw.rect(GUI.screen, (255, 255, 255),
                             (self.x, self.y, self.width, self.height))

        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = ((self.x + (self.width / 2)),
                            (self.y + (self.height / 2)))
        GUI.screen.blit(text_surface, text_rect)


class Slider(GUI):
    def __init__(self, x, y, width, height, value, max_value, slider_ticks = []):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = value
        self.max_value = max_value
        self.slider_ticks = slider_ticks

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

    def drag_events(self):
        self.circle_origin_x = self.x + \
            int(self.width * (self.value / self.max_value))
        self.circle_origin_y = self.y + int(self.height / 2)

        if self.check_mouse_on_ball(self.circle_origin_x, self.circle_origin_y):
            if GUI.is_single_click:
                self.is_dragging_ball = True
                self.drag_origin_x = GUI.mouse[0]
                self.drag_origin_y = GUI.mouse[1]
        if self.is_dragging_ball and GUI.is_holding_down:
            self.circle_origin_x = GUI.mouse[0]
            self.circle_origin_x = clamp(
                self.circle_origin_x, self.x, self.x + self.width)
            self.value = (self.circle_origin_x - self.x) * \
                self.max_value / self.width
        else:
            self.is_dragging_ball = False
            if self.check_mouse_on_slider():
                if GUI.is_single_click:
                    self.circle_origin_x = GUI.mouse[0]
                    self.circle_origin_x = clamp(
                        self.circle_origin_x, self.x, self.x + self.width)
                    self.value = (self.circle_origin_x - self.x) * \
                        self.max_value / self.width
                    self.is_dragging_ball = True

    def display(self):
        for tick, score in self.slider_ticks:
            tick_origin_x = self.x + \
                int(self.width * (tick / self.max_value))
            tick_origin_y = self.y + int(self.height / 2)
            tick_color = (255, 255, 255)
            if score == 100:
                tick_color = (70, 255, 70)
            elif score == 50:
                tick_color = (255, 140, 70)
            elif score == 0:
                tick_color = (255, 70, 70)

            pygame.draw.rect(GUI.screen, tick_color,
                             (tick_origin_x, tick_origin_y, 2, self.height*3))


        pygame.draw.rect(GUI.screen, (255, 255, 255),
                         (self.x, self.y, self.width, self.height))

        self.drag_events()

        ball_size = 8 if self.is_dragging_ball else 7

        gfxdraw.aacircle(GUI.screen, self.circle_origin_x,
                         self.circle_origin_y, ball_size, (0, 255, 255))
        gfxdraw.filled_circle(GUI.screen, self.circle_origin_x,
                              self.circle_origin_y, ball_size, (0, 255, 255))
        gfxdraw.aacircle(GUI.screen, self.circle_origin_x,
                         self.circle_origin_y, ball_size - 2, (0, 0, 0))
        if self.is_dragging_ball:
            gfxdraw.filled_circle(GUI.screen, self.circle_origin_x,
                                  self.circle_origin_y, ball_size - 2, (0, 0, 0))

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


class KeyRectangle(GUI):
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size

        self.key_down = False

        GUI.elements.append(self)

    def set_key_down(self):
        self.key_down = True

    def set_key_up(self):
        self.key_down = False

    def display(self):
        if self.key_down:
            color = (255, 211, 0)
        else:
            color = (40, 40, 40)

        pygame.draw.rect(GUI.screen, color,
                         (self.x, self.y, self.size, self.size), 0)


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
                               self.y + 10 + (index * self.font_size))

            labels.append(tmp_label)
            label_rects.append(tmp_rect)
        for i in range(len(labels)):
            GUI.screen.blit(labels[i], label_rects[i])
