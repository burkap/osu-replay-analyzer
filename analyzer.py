from utils.replay_parser import ReplayParser
from utils.beatmap import Beatmap
import numpy as np
import matplotlib.pyplot as plt
import time


class Analyzer:
    """
        replay_file     -- replay.file  (.osr)
        beatmap_file    -- beatmap file (.osu)

    """

    def __init__(self, replay_file: str, beatmap_file: str):
        self.play_parser = ReplayParser(replay_file)
        self.beatmap_parser = Beatmap(beatmap_file)

        self.current_frame = self.play_parser.frames[0]
        self.prev_frame = self.play_parser.frames[0]

        self.current_hitobject = self.beatmap_parser.hitobjects[0]
        self.prev_hitobject = self.beatmap_parser.hitobjects[0]

        self.frames_iterator = iter(self.play_parser.frames)
        self.hitobjects_iterator = iter(self.beatmap_parser.hitobjects)
        self.current_frame_hit = False
        self.count300 = 0
        self.count100 = 0
        self.count50 = 0
        self.countmiss = 0
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

        ####################################################
        # plotting members
        self.p_frame_count = 10
        self.fig, self.ax = plt.subplots()
        self.p_lines = []
        for _ in range(self.p_frame_count):
            self.p_lines.append(self.ax.plot(0, 0, 'b-')[0])
        self.p_hitcircle = plt.Circle((0, 0), self.circle_radius, color='k')

        self.frames_x = []
        self.frames_y = []
        # plotting init
        plt.ion()
        self.ax.set_xlim([0, 512])
        self.ax.set_ylim([0, 384])
        self.ax.add_artist(self.p_hitcircle)
        ####################################################

    def next_frame(self):
        self.prev_frame = self.current_frame
        self.current_frame = next(self.frames_iterator)

    def next_hitobject(self):
        self.prev_hitobject = self.current_hitobject
        self.current_hitobject = next(self.hitobjects_iterator)

    def check_if_hit(self, frame, hitobject):
        diff = pow(frame.x-hitobject.x, 2)+pow(frame.y-(384-hitobject.y), 2)
        return (pow(diff, 0.5) < self.circle_radius)

    def get_ms_delay(self, frame, hitobject):
        diff = hitobject.time-frame.time
        #print(diff)
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

    def draw_plot(self):
        self.frames_x.append(self.current_frame.x)
        self.frames_y.append(self.current_frame.y)
        self.frames_x = self.frames_x[-self.p_frame_count:]
        self.frames_y = self.frames_y[-self.p_frame_count:]

        for i in range(self.p_frame_count):
            self.p_lines[i].remove()
            self.p_lines[i], = self.ax.plot(self.frames_x, self.frames_y, 'b-')

        self.p_hitcircle.center = self.current_hitobject.x, 384-self.current_hitobject.y
        if self.check_if_hit(self.current_frame, self.current_hitobject):
            self.p_hitcircle.set_color('g')
        else:
            self.p_hitcircle.set_color('b')
        plt.show()
        plt.pause(0.0001)

    def analyze_for_relax(self, draw_plot: bool, show_outside: bool):
        """
            draw_plot:      bool-- ...
            show_outside:   bool-- ...

        """
        f = open("out.txt", "w")
        if show_outside:
            self.ax.set_xlim([-128, 512 + 128])
            self.ax.set_ylim([-64 * 3 / 2, 384 + 64 * 3 / 2])
        while True:
            if draw_plot:
                self.draw_plot()
            print("Current frame: {} | Next hitobject: {} | Previous hitobject: {}".format(
                self.current_frame.time, self.current_hitobject.time, self.prev_hitobject.time), file=f)
            if self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                pass
            if not self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                self.current_frame_hit = self.check_if_hit(
                    self.current_frame, self.current_hitobject)
                if self.current_frame_hit:
                    self.get_ms_delay(self.current_frame,
                                      self.current_hitobject)
            if self.current_frame.time < self.current_hitobject.time:
                self.next_frame()
            else:
                self.next_frame()
                self.next_hitobject()
