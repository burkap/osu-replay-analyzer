from utils.replay_parser import ReplayParser
from utils.beatmap import Beatmap
from utils.gui import GUI, Hitcircle, Cursor, Button, Slider, DebugBox, OSU, Hitobject_Slider, TextBox, CursorTrail, \
    KeyRectangle
import time
import numpy as np
from utils.mathhelper import clamp, get_closest_as_index, is_inside_radius, Vec2, ms_to_time
from pygame.constants import *


class Analyzer:
    """
        replay_file     -- replay.file  (.osr)
        beatmap_file    -- beatmap file (.osu)
    """

    def __init__(self, replay_file: str, beatmap_file: str):
        self.play_parser = ReplayParser(replay_file)
        self.beatmap_parser = Beatmap(beatmap_file)

        self._frames_count = len(self.play_parser.frames)
        self._hitobjects_count = len(self.beatmap_parser.hitobjects)

        self.current_frame_index = 0
        self.current_hitobject_index = 0

        self.current_ms = self.play_parser.frames[0].time
        self.current_frame = self.play_parser.frames[self.current_frame_index]
        self.prev_frame = self.play_parser.frames[self.current_frame_index]

        self.current_hitobject = self.beatmap_parser.hitobjects[self.current_frame_index]
        self.prev_hitobject = self.beatmap_parser.hitobjects[self.current_frame_index]

        self.current_frame_hit = False
        self.count300 = 0
        self.count100 = 0
        self.count50 = 0
        self.countmiss = 0

        self.trail_length = 10
        self.anim_speed = 1
        self.running = True
        # set cs
        cs = self.beatmap_parser.difficulty["CircleSize"]
        if self.play_parser.mods & 2:  # easy
            cs = cs / 2
        elif self.play_parser.mods & 16:  # hardrock
            cs = min(cs * 1.3, 10)
        self.circle_radius = 54.4 - 4.48 * cs

        # set od
        od = self.beatmap_parser.difficulty["OverallDifficulty"]
        if self.play_parser.mods & 2:  # easy
            od = od / 2
        elif self.play_parser.mods & 16:  # hardrock
            od = min(od * 1.4, 10)

        # hit windows
        self.hit_50 = (400 - (20 * od)) / 2
        self.hit_100 = (280 - (16 * od)) / 2
        self.hit_300 = (160 - (12 * od)) / 2

    def switch_running(self):
        self.running = not self.running

    def switch_speed_to_dt(self):
        self.anim_speed = 1.5

    def switch_speed_to_ht(self):
        self.anim_speed = 0.5

    def switch_speed_to_nm(self):
        self.anim_speed = 1

    def get_trailing_frames(self, n):
        frames = []
        for i in range(0, n):
            f = self.get_relative_frame(-i)
            frames.append(f)
        return frames

    def get_upcoming_frames(self, n):
        frames = []
        for i in range(0, n):
            f = self.get_relative_frame(+i)
            frames.append(f)
        return frames

    def get_relative_frame(self, r_index: int):
        abs_frame_index = self.current_frame_index + r_index
        abs_frame_index = clamp(abs_frame_index, 0, self._frames_count - 1)
        return self.play_parser.frames[abs_frame_index]

    def go_to_prev_ms(self):
        self.current_ms = clamp(self.current_ms - 1, 0, self.play_parser.frames[-1].time)

    def go_to_next_ms(self):
        self.current_ms = clamp(self.current_ms + 1, 0, self.play_parser.frames[-1].time)

    def go_to_next_ms_faster(self):
        self.current_ms = clamp(self.current_ms + 10, 0, self.play_parser.frames[-1].time)

    def go_to_prev_ms_faster(self):
        self.current_ms = clamp(self.current_ms - 10, 0, self.play_parser.frames[-1].time)


    def go_to_prev_frame(self):
        self.current_frame_index = clamp(
            self.current_frame_index - 1, 0, self._frames_count - 1)
        self.prev_frame = self.play_parser.frames[self.current_frame_index - 1]
        self.current_frame = self.play_parser.frames[self.current_frame_index]

    def go_to_next_frame(self):
        self.current_frame_index = clamp(
            self.current_frame_index + 1, 0, self._frames_count - 1)
        self.prev_frame = self.play_parser.frames[self.current_frame_index - 1]
        self.current_frame = self.play_parser.frames[self.current_frame_index]

    def set_current_ms(self, ms):
        self.current_ms = ms

    def set_current_frame(self, index):
        self.current_frame_index = index
        try:
            self.prev_frame = self.play_parser.frames[self.current_frame_index - 1]
            self.current_frame = self.play_parser.frames[self.current_frame_index]
        except IndexError:
            print("Index error")

    def set_current_hitobject(self, index):
        self.current_hitobject_index = index
        try:
            self.prev_hitobject = self.beatmap_parser.hitobjects[self.current_hitobject_index - 1]
            self.current_hitobject = self.beatmap_parser.hitobjects[self.current_hitobject_index]
        except IndexError:
            print("Index error")

    def go_to_next_hitobject(self):
        self.current_hitobject_index = clamp(
            self.current_hitobject_index + 1, 0, self._hitobjects_count - 1)
        self.prev_hitobject = self.beatmap_parser.hitobjects[self.current_hitobject_index - 1]
        self.current_hitobject = self.beatmap_parser.hitobjects[self.current_hitobject_index]

    def get_ms_delay(self, frame, hitobject):
        diff = frame.time - hitobject.time
        return diff

    def get_score(self, diff, is_slider):
        diff = abs(diff)
        if is_slider:
            if diff >= self.hit_50:
                return 0
            else:
                return 300
        else:
            if diff >= self.hit_50:
                return 0
            elif diff >= self.hit_100:
                return 50
            elif diff >= self.hit_300:
                return 100
            else:
                return 300
    def get_scores(self):
        ######################################-------------|score is integer value 300, 100, 50, or 0 if miss
        # Running over whole play for once                 v
        scores = []  # this gets (frame, hitobject, diff, score)
        while True:
            current_pos_frame = (self.current_frame.x, self.current_frame.y)
            current_pos_hitobject = (self.current_hitobject.x, 384 -
                                     self.current_hitobject.y if (
                                         self.play_parser.mods & 16) else self.current_hitobject.y)
            if is_inside_radius(current_pos_frame, current_pos_hitobject, self.circle_radius):
                diff_ms = self.get_ms_delay(
                    self.current_frame, self.current_hitobject)
                if ((not self.prev_frame.k1_pressed) and self.current_frame.k1_pressed) or (
                        (not self.prev_frame.k2_pressed) and self.current_frame.k2_pressed):
                    if -self.hit_50 < diff_ms < self.hit_50:
                        scores.append((self.current_frame, self.current_hitobject, diff_ms, self.get_score(
                            diff_ms, self.current_hitobject.type & 2)))
                        if self.current_hitobject.time == self.beatmap_parser.hitobjects[-1].time:
                            break
                        self.go_to_next_hitobject()

            if self.current_frame.time < self.current_hitobject.time + self.hit_50:
                self.go_to_next_frame()
            else:
                diff_ms = self.get_ms_delay(
                    self.current_frame, self.current_hitobject)
                scores.append((self.current_frame, self.current_hitobject, diff_ms, self.get_score(
                    diff_ms, self.current_hitobject.type & 2)))
                if self.current_hitobject.time == self.beatmap_parser.hitobjects[-1].time:
                    break
                self.go_to_next_frame()
                self.go_to_next_hitobject()

        for _, _, _, score in scores:
            if score == 300:
                self.count300 += 1
            elif score == 100:
                self.count100 += 1
            elif score == 50:
                self.count50 += 1
            elif score == 0:
                self.countmiss += 1
        return scores
        #
        #######

    def run(self):
        """
            # to-do:
            # draw_gui:      bool-- ...
        """
        scores = self.get_scores()

        # GUI code starts here
        self.set_current_frame(0)
        self.set_current_hitobject(0)

        start_time = time.time()
        play_area_width, play_area_height = (800, 600)
        padding_width, padding_height = (130, 60)
        gui_width, gui_height = (
            play_area_width + padding_width * 2, play_area_height + padding_height * 2)
        gui = GUI(
            play_area_width,
            play_area_height,
            padding_width,
            padding_height)
        gui.play_music()
        osu = OSU(self.current_frame, (self.play_parser.mods & 16))
        hc = []
        sliders = []
        try:
            for index, h in enumerate(self.beatmap_parser.hitobjects):
                hc.append(Hitcircle(
                    h.x,
                    384 - h.y if osu.is_hardrock else h.y,
                    h.time,
                    scores[index],
                    self.circle_radius))
                if h.type & 2:
                    sliders.append(
                        Hitobject_Slider(
                            [
                                Vec2(
                                    i.x,
                                    384 - i.y if osu.is_hardrock else i.y) for i in h.curve_points],
                            self.circle_radius,
                            h.time,
                            h.duration))
        except:
            pass  # todo
        cursor = Cursor((0, 0))
        cursor_trail = CursorTrail()
        button_pause = Button(
            30,
            250,
            50,
            30,
            "Pause",
            self.switch_running)

        key1_rectangle = KeyRectangle(
            play_area_width + padding_width * 2 - 70, 315, 50)
        key2_rectangle = KeyRectangle(
            play_area_width + padding_width * 2 - 70, 370, 50)

        button_dt = Button(30, 100, 50, 30, "DT", self.switch_speed_to_dt)
        button_nm = Button(30, 150, 50, 30, "NM", self.switch_speed_to_nm)
        button_ht = Button(30, 200, 50, 30, "HT", self.switch_speed_to_ht)

        slider = Slider(padding_width + 35, gui_height - 50, gui_width - padding_width * 2 - 70, 5,
                        self.current_ms,
                        self.play_parser.frames[-1].time)
        time_display = TextBox(padding_width - 10, gui_height -
                               58, 50, 20, str(self.current_frame.time))

        debuglog = DebugBox(gui_width - 125, 10, 120, 200)
        instructions_box = DebugBox(gui_width - 125, 220, 120, 70)
        instructions_box.add_text("SPACE - play/pause")
        instructions_box.add_text("X - toggle markers ")
        instructions_box.add_text("RIGHT - next frame")
        instructions_box.add_text("LEFT - prev frame")
        instructions_box.add_text("CTRL to skip frames faster")

        ##########
        # Keyboard Events
        gui.add_single_press_event([K_SPACE], self.switch_running)
        gui.add_single_press_event([K_RIGHT], self.go_to_next_ms)
        gui.add_single_press_event([K_LEFT], self.go_to_prev_ms)
        gui.add_single_press_event([K_x], cursor_trail.toggle_show_markers)

        # prev is 1 more than next because there's one go_to_next_frame() at the end of loop
        gui.add_holding_down_event([K_RIGHT, K_LCTRL], self.go_to_next_ms_faster)
        gui.add_holding_down_event([K_LEFT, K_LCTRL], self.go_to_prev_ms_faster)
        #
        ########
        nth_frame = 0
        while True:
            if nth_frame == 10:
                gui.set_music_pos(self.current_frame.time)
                nth_frame =0
            nth_frame += 1

            osu.set_current_frame(self.current_frame)
            time_display.set_text(ms_to_time(self.current_frame.time))
            debuglog.clear()
            debuglog.add_text(f"Circle Radius: {round(self.circle_radius)}")
            debuglog.add_text(f"nth_frame: {nth_frame}")
            debuglog.add_text(f"Frame index: {self.current_frame_index}")
            debuglog.add_text(f"Frame time:{self.current_frame.time}")
            debuglog.add_text(f"Current time:{self.current_ms}")
            debuglog.add_text(
                f"Cur. Hit Obj. time: {self.current_hitobject.time}")
            debuglog.add_text(
                f"Prev. Hit Obj. time: {self.prev_hitobject.time}")
            debuglog.add_text(
                f"Hit Object index: {self.current_hitobject_index}")

            debuglog.add_text(
                f"Music pos: {gui.get_music_pos()}")

            debuglog.add_text(
                f"")
            debuglog.add_text(
                f"       Hit Windows       ")
            debuglog.add_text(f"{self.hit_300} {self.hit_100} {self.hit_50}")

            debuglog.add_text(
                f"")
            debuglog.add_text(f"Count of scores: {len(scores)}")
            debuglog.add_text(f"Speed: x{self.anim_speed}")

            debuglog.add_text(
                f"")
            debuglog.add_text(f"300: {self.count300} 100: {self.count100}")
            debuglog.add_text(f"50: {self.count50} X: {self.countmiss}")

            frame_time_diff = max(1, self.current_frame.time - self.prev_frame.time)
            to_next_frame_time_ratio = (self.current_ms - self.prev_frame.time) / frame_time_diff

            debuglog.add_text(f"time ratio:{to_next_frame_time_ratio:.2f}")
            button_pause.set_text("Pause" if self.running else "Play")
            gui.draw()

            gui.clock.tick(60 * self.anim_speed)

            if self.current_frame.k1_pressed:
                key1_rectangle.set_key_down()
            else:
                key1_rectangle.set_key_up()

            if self.current_frame.k2_pressed:
                key2_rectangle.set_key_down()
            else:
                key2_rectangle.set_key_up()

            if slider.is_dragging_ball:
                self.set_current_ms(int(slider.get_value()))
                self.set_current_frame(get_closest_as_index(
                    self.play_parser.frame_times, int(slider.get_value())))
                self.set_current_hitobject(get_closest_as_index(
                    [i.time for i in self.beatmap_parser.hitobjects], int(slider.get_value())))
            else:
                slider.set_value(self.current_ms)

            cursor_x = np.interp(self.current_ms, [self.prev_frame.time, self.current_frame.time],
                                           [self.prev_frame.x, self.current_frame.x])
            cursor_y = np.interp(self.current_ms, [self.prev_frame.time, self.current_frame.time],
                                           [self.prev_frame.y, self.current_frame.y])
            cursor.set_cursor_position(cursor_x, cursor_y)
            cursor_trail.set_trailing_points(
                self.get_trailing_frames(self.trail_length))
            cursor_trail.set_leading_points(
                self.get_upcoming_frames(self.trail_length * 2 // 3))
            #   GUI CODE ENDS HERE
            #######################

            if self.current_ms >= self.current_frame.time:
                self.go_to_next_frame()
            elif self.current_ms < self.prev_frame.time:
                self.go_to_prev_frame()
            if not self.current_frame.time < self.current_hitobject.time:
                self.go_to_next_hitobject()

            if self.running:
                gui.unpause_music()
                self.go_to_next_ms()
            else:
                gui.pause_music()
