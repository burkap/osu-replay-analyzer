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

        self.current_frame=self.play_parser.frames[0]
        self.prev_frame=self.play_parser.frames[0]

        self.current_hitobject=self.beatmap_parser.hitobjects[0]
        self.prev_hitobject=self.beatmap_parser.hitobjects[0]
        
        self.frames_iterator=iter(self.play_parser.frames)
        self.hitobjects_iterator=iter(self.beatmap_parser.hitobjects)
        self.current_frame_hit=False
        self.count300 = 0
        self.count100 = 0
        self.count50 = 0
        self.countmiss = 0
        # set cs
        cs = self.beatmap_parser.difficulty["CircleSize"]
        if self.play_parser.mods & 2:                   #easy
           cs = cs/2
        elif self.play_parser.mods & 16:                #hardrock
            cs = min(cs*1.3, 10)
        self.circle_radius = 54.4 - 4.48 * cs
        print(self.circle_radius)
        
        # set od
        self.overall_diff = self.beatmap_parser.difficulty["OverallDifficulty"] 
        if self.play_parser.mods & 2:                               #easy
            self.overall_diff = self.overall_diff/2
        elif self.play_parser.mods & 16:                            #hardrock
            self.overall_diff = min(self.overall_diff*1.4, 10)

        # hit windows
        self.hit_50  = 400 - (20*self.overall_diff)
        self.hit_100 = 280 - (16*self.overall_diff)
        self.hit_300 = 160 - (12-self.overall_diff)
        if self.play_parser.mods & 256:                             #halftime
            self.hit_50  = 400 - (20*self.overall_diff)*4/3
            self.hit_100 = 280 - (16*self.overall_diff)*4/3
            self.hit_300 = 160 - (12-self.overall_diff)*4/3
        elif self.play_parser.mods & 64:                            #doubletime
            self.hit_50  = 400 - (20*self.overall_diff)*2/3
            self.hit_100 = 280 - (16*self.overall_diff)*2/3
            self.hit_300 = 160 - (12-self.overall_diff)*2/3

        ####################################################
        # plotting members
        self.fig, self.ax = plt.subplots()
        self.p1, = self.ax.plot(self.current_frame.x, 'b.')
        self.p_hitcircle = plt.Circle((0, 0), self.circle_radius, color = 'k')
        # plotting init
        plt.ion()
        self.ax.set_xlim([0,512])
        self.ax.set_ylim([0,384])
        self.ax.add_artist(self.p_hitcircle)
        ####################################################

    def next_frame(self):
        self.prev_frame = self.current_frame
        self.current_frame = next(self.frames_iterator)

    def next_hitobject(self):
        self.prev_hitobject = self.current_hitobject
        self.current_hitobject = next(self.hitobjects_iterator)
    
    def check_if_hit(self, frame, hitobject):
        diff = pow(frame.x-hitobject.x,2)+pow(frame.y-(384-hitobject.y),2)
        return (pow(diff,0.5)<self.circle_radius)

    def get_ms_delay(self,frame,hitobject):
        diff = hitobject.time-frame.time
        print(diff)
        diff = abs(diff)
        if diff >= self.hit_50:
            #miss
            self.countmiss+=1
        elif diff >= self.hit_100:
            #hit 50
            self.count50+=1
        elif diff >= self.hit_300:
            #hit 100
            self.count300+=1
        else:
            #hit 300
            self.count300+=1
    
    def draw_plot(self):
        self.p1.remove()
        arrx = [self.prev_frame.x,self.current_frame.x]
        arry = [self.prev_frame.y,self.current_frame.y]
        self.p1, = self.ax.plot(arrx, arry, 'bo')
        """if self.current_frame.k1_pressed:
            self.p1, = self.ax.plot(arrx, arry, 'bo')
        else:
            self.p1, = self.ax.plot(arrx, arry, 'ro')
        """
        self.p_hitcircle.center = self.current_hitobject.x, 384-self.current_hitobject.y
        if self.check_if_hit(self.current_frame,self.current_hitobject):
            self.p_hitcircle.set_color('g')
        else:
            self.p_hitcircle.set_color('b')
        plt.show()
        plt.pause(0.0001) #Note this correction

    def analyze_for_relax(self):
        ## Note this correction
        f = open("out.txt", "w")
        while True:
            self.draw_plot()
            print("Current frame: {} | Next hitobject: {} | Previous hitobject: {}".format(self.current_frame.time, self.current_hitobject.time, self.prev_hitobject.time),file= f)
            if self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                pass
            if not self.prev_frame.k1_pressed and self.current_frame.k1_pressed:
                self.current_frame_hit = self.check_if_hit(self.current_frame, self.current_hitobject)
                if self.current_frame_hit:
                    self.get_ms_delay(self.current_frame, self.current_hitobject)
            if self.current_frame.time < self.current_hitobject.time:
                self.next_frame()
            else:
                self.next_frame()
                self.next_hitobject()

