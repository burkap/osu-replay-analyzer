from utils.replay_parser import ReplayParser
from utils.beatmap import Beatmap
from utils.gui import GUI, Hitcircle, Cursor, Button, Slider, DebugBox, OSU, Hitobject_Slider
import time
from utils.mathhelper import clamp, get_closest_as_index, is_inside_radius, Vec2


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
        print(f"Circle Radius: {self.circle_radius}")

        # set od
        od = self.beatmap_parser.difficulty["OverallDifficulty"]
        if self.play_parser.mods & 2:  # easy
            od = od / 2
        elif self.play_parser.mods & 16:  # hardrock
            od = min(od * 1.4, 10)

        # hit windows
        self.hit_50 = 400 - (20 * od)
        self.hit_100 = 280 - (16 * od)
        self.hit_300 = 160 - (12 * od)
        if self.play_parser.mods & 256:  # halftime
            self.hit_50 = self.hit_100 * 4 / 3
            self.hit_100 = self.hit_100 * 4 / 3
            self.hit_300 = self.hit_300 * 4 / 3
        elif self.play_parser.mods & 64:  # doubletime
            self.hit_50 = self.hit_100 * 2 / 3
            self.hit_100 = self.hit_100 * 2 / 3
            self.hit_300 = self.hit_300 * 2 / 3

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
            frames.append((f.x, f.y))
        return frames

    def get_upcoming_frames(self, n):
        frames = []
        for i in range(0, n):
            f = self.get_relative_frame(+i)
            frames.append((f.x, f.y))
        return frames

    def get_relative_frame(self, r_index: int):
        abs_frame_index = self.current_frame_index + r_index
        abs_frame_index = clamp(abs_frame_index, 0, self._frames_count - 1)
        return self.play_parser.frames[abs_frame_index]

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
        diff = hitobject.time - frame.time
        # print(diff)
        diff = abs(diff)
        if diff >= self.hit_50:
            # miss
            self.countmiss += 1
        elif diff >= self.hit_100:
            # hit 50
            self.count50 += 1
        elif diff >= self.hit_300:
            # hit 100
            self.count300 += 1
        else:
            # hit 300
            self.count300 += 1

    def analyze_for_relax(self):
        """
            draw_plot:      bool-- ...
            show_outside:   bool-- ...
        """
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

        osu = OSU(self.current_frame, (self.play_parser.mods & 16))
        hc = []
        sliders = []
        for h in self.beatmap_parser.hitobjects:
            hc.append(Hitcircle(
                h.x,
                384 - h.y if osu.is_hardrock else h.y,
                h.time,
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
        cursor = Cursor((0, 0), show_path=True)
        button_pause = Button(
            30,
            250,
            50,
            30,
            "Pause",
            self.switch_running)

        button_dt = Button(30, 100, 50, 30, "DT", self.switch_speed_to_dt)
        button_nm = Button(30, 150, 50, 30, "NM", self.switch_speed_to_nm)
        button_ht = Button(30, 200, 50, 30, "HT", self.switch_speed_to_ht)

        slider = Slider(padding_width + 35, gui_height - 50, gui_width - padding_width * 2 - 70, 5, self.current_frame.time,
                        self.play_parser.frames[-1].time)

        debuglog = DebugBox(gui_width - 125, 10, 120, 200)
        f = open("out.txt", "w")
        while True:
            osu.set_current_frame(self.current_frame)
            debuglog.clear()
            debuglog.add_text(f"Frame index: {self.current_frame_index}")
            debuglog.add_text(
                f"Hit Object index: {self.current_hitobject_index}")
            debuglog.add_text(f"Speed: x{self.anim_speed}")
            button_pause.set_text("Pause" if self.running else "Play")

            gui.draw()

            end_time = time.time()
            next_frame = self.get_relative_frame(1)
            delay = end_time - start_time
            time_difference = (
                next_frame.time - self.current_frame.time) * 0.001
            wait_for = max(0.0001, time_difference - delay) / self.anim_speed

            time.sleep(wait_for)
            start_time = time.time()

            if slider.is_dragging_ball:
                self.set_current_frame(get_closest_as_index(
                    self.play_parser.frame_times, int(slider.get_value())))
                self.set_current_hitobject(get_closest_as_index(
                    [i.time for i in self.beatmap_parser.hitobjects], int(slider.get_value())))
            else:
                slider.set_value(
                    self.play_parser.frames[self.current_frame_index].time)

            cursor.set_cursor_position(self.current_frame.x,
                                       self.current_frame.y)
            cursor.set_trail_points(
                self.get_trailing_frames(self.trail_length))

            cursor.set_path_points(
                self.get_upcoming_frames(self.trail_length * 2 // 3))

            print("Current frame: {} | Next hitobject: {} | Previous hitobject: {}".format(
                self.current_frame.time, self.current_hitobject.time, self.prev_hitobject.time), file=f)

            if self.running:
                if self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                    pass
                if not self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                    self.current_frame_hit = is_inside_radius(
                        (self.current_frame.x, self.current_frame.y),
                        (self.current_hitobject.x, self.current_hitobject.y),
                        self.circle_radius)
                    if self.current_frame_hit:
                        self.get_ms_delay(self.current_frame,
                                          self.current_hitobject)
                if self.current_frame.time < self.current_hitobject.time:
                    self.go_to_next_frame()
                else:
                    self.go_to_next_frame()
                    self.go_to_next_hitobject()
