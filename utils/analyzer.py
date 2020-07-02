from utils.replay_parser import ReplayParser
from utils.beatmap import Beatmap
from utils.gui import GUI, Hitcircle, Cursor, Button
import time


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


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
            od = od/2
        elif self.play_parser.mods & 16:  # hardrock
            od = min(od * 1.4, 10)

        # hit windows
        self.hit_50 = 400 - (20 * od)
        self.hit_100 = 280 - (16 * od)
        self.hit_300 = 160 - (12 * od)
        if self.play_parser.mods & 256:  # halftime
            self.hit_50 = self.hit_100 * 4/3
            self.hit_100 = self.hit_100 * 4/3
            self.hit_300 = self.hit_300 * 4/3
        elif self.play_parser.mods & 64:  # doubletime
            self.hit_50 = self.hit_100 * 2/3
            self.hit_100 = self.hit_100 * 2/3
            self.hit_300 = self.hit_300 * 2/3

    def switch_running(self):
        self.running = not self.running

    def get_trailing_frames(self, n):
        frames = []
        for i in range(0, n):
            f = self.get_relative_frame(-i)
            frames.append((f.x, f.y))
        return frames

    def get_relative_frame(self, r_index: int):
        # TODO: add boundary checks
        return self.play_parser.frames[self.current_frame_index+r_index]

    def go_to_prev_frame(self):
        self.current_frame_index = clamp(
            self.current_frame_index-1, 0, self._frames_count-1)
        self.prev_frame = self.play_parser.frames[self.current_frame_index-1]
        self.current_frame = self.play_parser.frames[self.current_frame_index]

    def go_to_next_frame(self):
        self.current_frame_index = clamp(
            self.current_frame_index+1, 0, self._frames_count-1)
        self.prev_frame = self.play_parser.frames[self.current_frame_index-1]
        self.current_frame = self.play_parser.frames[self.current_frame_index]

    def go_to_next_hitobject(self):
        self.current_hitobject_index = clamp(
            self.current_hitobject_index+1, 0, self._hitobjects_count-1)
        self.prev_hitobject = self.beatmap_parser.hitobjects[self.current_hitobject_index-1]
        print(self.current_hitobject_index)
        self.current_hitobject = self.beatmap_parser.hitobjects[self.current_hitobject_index]

    def check_if_hit(self, frame, hitobject):
        diff = pow(frame.x-hitobject.x, 2)+pow(frame.y-(384-hitobject.y), 2)
        return (pow(diff, 0.5) < self.circle_radius)

    def get_ms_delay(self, frame, hitobject):
        diff = hitobject.time-frame.time
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
        gui = GUI(512, 384)

        hc = Hitcircle(0, 0, self.circle_radius)
        cursor = Cursor((0, 0))
        button1 = Button(256-25, 300, 50, 20, "Pause", self.switch_running)
        f = open("out.txt", "w")
        while True:
            button1.set_text("Pause" if self.running else "Play")
            hc.set_position(self.current_hitobject.x,
                            384-self.current_hitobject.y)

            if self.check_if_hit(self.current_frame, self.current_hitobject):
                hc.set_color((0, 255, 0))
            else:
                hc.set_color((255, 0, 0))
            cursor.set_cursor_position(self.current_frame.x,
                                       self.current_frame.y)
            cursor.set_trail_points(
                self.get_trailing_frames(self.trail_length))
            gui.draw()
            time.sleep(0.01)
            print("Current frame: {} | Next hitobject: {} | Previous hitobject: {}".format(
                self.current_frame.time, self.current_hitobject.time, self.prev_hitobject.time), file=f)

            if self.running:
                if self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                    pass
                if not self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                    self.current_frame_hit = self.check_if_hit(
                        self.current_frame, self.current_hitobject)
                    if self.current_frame_hit:
                        self.get_ms_delay(self.current_frame,
                                          self.current_hitobject)
                if self.current_frame.time < self.current_hitobject.time:
                    self.go_to_next_frame()
                else:
                    self.go_to_next_frame()
                    self.go_to_next_hitobject()
