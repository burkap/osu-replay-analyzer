from utils.replay_parser import ReplayParser
from utils.osu_db_parser import DatabaseParser
from utils.beatmap import Beatmap
from utils.gui import GUI, Hitcircle, Cursor, Button, Slider, DebugBox, OSU, Hitobject_Slider, TextBox, CursorTrail, \
    KeyRectangle
import time
import numpy as np
from utils.mathhelper import clamp, get_closest_as_index, is_inside_radius, Vec2, ms_to_time
from pygame.constants import *
import os


class Analyzer:
    """
        replay_file     -- replay.file  (.osr)
        beatmap_file    -- beatmap file (.osu)
    """

    def __init__(self, replay_file: str, osu_path: str):
        songs_folder = os.path.join(osu_path, "Songs")
        db_file = os.path.join(osu_path, "osu!.db")

        self.play_parser = ReplayParser(replay_file)

        self.db_parser = DatabaseParser(db_file)
        bm = self.db_parser.beatmaps[self.play_parser.beatmap_md5.decode("UTF-8")]  # Folder, *.mp3, *.osu
        beatmap_folder = os.path.join(songs_folder, bm[0])
        beatmap_osu = os.path.join(beatmap_folder, bm[2])
        self.music_path = os.path.join(beatmap_folder, bm[1])

        self.beatmap_parser = Beatmap(beatmap_osu)

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
        self.music_catchup_boost = 1
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

    def change_speed(self, speed, gui):
        self.anim_speed = speed
        gui.change_play_speed(self.anim_speed)
        gui.set_music_pos(self.current_frame.time)

    def get_trailing_frames(self, n):
        return self.play_parser.frames[self.current_frame_index - n: self.current_frame_index]

    def get_upcoming_frames(self, n):
        return self.play_parser.frames[self.current_frame_index: self.current_frame_index + n]

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
        # -------------|score is integer value 300, 100, 50, or 0 if miss
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
            self.music_path,
            padding_width,
            padding_height)
        gui.play_music()
        osu = OSU(self.current_frame, (self.play_parser.mods & 16))
        hc = []
        sliders = []
        try:
            for index, h in enumerate(self.beatmap_parser.hitobjects):
                hc.append(Hitcircle(h, scores[index][3], self.circle_radius))
                if h.type & 2:
                    sliders.append(Hitobject_Slider(h, self.circle_radius, True))
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

        button_dt = Button(30, 100, 50, 30, "DT", self.change_speed, 1.5, gui)
        button_nm = Button(30, 150, 50, 30, "NM", self.change_speed, 1, gui)
        button_ht = Button(30, 200, 50, 30, "HT", self.change_speed, 0.5, gui)

        slider = Slider(padding_width + 35, gui_height - 50, gui_width - padding_width * 2 - 70, 5,
                        gui.get_music_pos(),
                        self.play_parser.frames[-1].time, [(i[0].time, i[3]) for i in scores if i[3] != 300])
        volume_slider = Slider(30, 70, 95, 5, gui.volume, 1)
        volume_display = TextBox(5, 63, 20, 20, str(
            int(volume_slider.get_value() * 100)) + "%")
        time_display = TextBox(padding_width - 10, gui_height -
                               58, 50, 20, str(self.current_frame.time))

        ms_arr = []
        ms_display = TextBox(gui_width - padding_width - 40, gui_height -padding_height - 20, 50, 20, "0")
        debuglog = DebugBox(gui_width - 125, 10, 120, 250)
        instructions_box = DebugBox(gui_width - 125, gui_height - 250, 120, 150)
        instructions_box.add_text("SPACE - play/pause")
        instructions_box.add_text("X - toggle markers ")
        instructions_box.add_text("M - mute on/off")
        instructions_box.add_text("RIGHT - next frame")
        instructions_box.add_text("LEFT - prev frame")
        instructions_box.add_text("CTRL - skip frames faster")

        ##########
        # Keyboard Events
        ####

        def toggle_mute():
            if toggle_mute.is_muted:
                volume_slider.set_value(toggle_mute.old_value)
                toggle_mute.is_muted = False
            else:
                toggle_mute.old_value = volume_slider.get_value()
                volume_slider.set_value(0)
                toggle_mute.is_muted = True

        toggle_mute.is_muted = False
        toggle_mute.old_value = 0.3

        ####
        gui.add_single_press_event([K_SPACE], self.switch_running)
        # to-do V
        # gui.add_single_press_event([K_RIGHT], self.go_to_next_ms)
        # gui.add_single_press_event([K_LEFT], self.go_to_prev_ms)
        gui.add_single_press_event([K_x], cursor_trail.toggle_show_markers)
        gui.add_single_press_event([K_m], toggle_mute)
        #
        #####################

        # prev is 1 more than next because there's one go_to_next_frame() at the end of loop
        # to-do V
        """ gui.add_holding_down_event(
            [K_RIGHT, K_LCTRL], self.go_to_next_ms_faster)
        gui.add_holding_down_event(
            [K_LEFT, K_LCTRL], self.go_to_prev_ms_faster)
        """
        #
        ########
        gui.pause_music()
        gui.set_music_pos(gui.get_music_pos())
        while True:
            osu.set_current_frame(self.current_frame)
            time_display.set_text(ms_to_time(self.current_frame.time))
            ms_arr.append(abs(self.current_frame.time - gui.get_music_pos()))
            ms_arr=ms_arr[-10:]
            ms_display.set_text(str(sum(ms_arr)/len(ms_arr)))
            volume_display.set_text(
                str(int(volume_slider.get_value() * 100)) + "%")
            gui.set_volume(volume_slider.get_value())
            debuglog.clear()
            debuglog.add_text(f"Circle Radius: {round(self.circle_radius)}")
            debuglog.add_text(f"Frame index: {self.current_frame_index}")
            debuglog.add_text(f"Frame time:{self.current_frame.time}")
            debuglog.add_text(
                f"Cur. Hit Obj. time: {self.current_hitobject.time}")
            debuglog.add_text(
                f"Prev. Hit Obj. time: {self.prev_hitobject.time}")
            debuglog.add_text(
                f"Hit Object index: {self.current_hitobject_index}")

            debuglog.add_text(
                f"Music pos: {gui.get_music_pos()}")
            debuglog.add_text(
                f"Music diff frame: {self.current_frame.time - gui.get_music_pos()}")
            debuglog.add_text(
                f"Music diff ms: {self.current_frame.time - gui.get_music_pos():.2f}")
            debuglog.add_text(
                f"Is running: {self.running}")

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
            button_pause.set_text("Pause" if self.running else "Play")

            gui.draw()

            gui.clock.tick(60)

            if self.current_frame.k1_pressed:
                key1_rectangle.set_key_down()
            else:
                key1_rectangle.set_key_up()

            if self.current_frame.k2_pressed:
                key2_rectangle.set_key_down()
            else:
                key2_rectangle.set_key_up()

            if slider.is_dragging_ball:
                self.set_current_frame(get_closest_as_index(
                    self.play_parser.frame_times, int(slider.get_value())))
                self.set_current_hitobject(get_closest_as_index(
                    [i.time for i in self.beatmap_parser.hitobjects], int(slider.get_value())))
                gui.set_music_pos(self.current_frame.time)
            else:
                slider.set_value(gui.get_music_pos())

            cursor_x = np.interp(gui.get_music_pos(), [self.prev_frame.time, self.current_frame.time],
                                 [self.prev_frame.x, self.current_frame.x])
            cursor_y = np.interp(gui.get_music_pos(), [self.prev_frame.time, self.current_frame.time],
                                 [self.prev_frame.y, self.current_frame.y])
            cursor.set_cursor_position(cursor_x, cursor_y)
            cursor_trail.set_trailing_points(
                self.get_trailing_frames(self.trail_length))
            cursor_trail.set_leading_points(
                self.get_upcoming_frames(self.trail_length * 2 // 3))
            #   GUI CODE ENDS HERE
            #######################

            self.set_current_frame(get_closest_as_index(self.play_parser.frame_times, gui.get_music_pos()))
            if self.running:
                gui.unpause_music()
            else:
                gui.pause_music()
                test = self.current_frame.time
