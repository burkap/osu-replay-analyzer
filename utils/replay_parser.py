from typing import Union
from io import BytesIO
from utils.leb128 import Uleb128
from lzma import decompress as lzma_decompress
from utils.frame import Frame


class ReplayParser:

    def __init__(self, replay_file: Union[str, BytesIO]):
        if isinstance(replay_file, str):
            with open(replay_file, "rb") as replay:
                self.replay_raw = BytesIO(replay.read())
        else:
            self.replay_raw = replay_file

        self.replay_raw.seek(0)
        self.game_mode = int.from_bytes(self.replay_raw.read(1), byteorder="little")
        self.version = int.from_bytes(self.replay_raw.read(4), byteorder="little")
        self.beatmap_md5 = self.read_string()
        self.player_name = self.read_string()
        self.replay_md5 = self.read_string()
        self.count300 = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.count100 = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.count50 = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.count_geki = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.count_katu = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.count_miss = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.score = int.from_bytes(self.replay_raw.read(4), byteorder="little")
        self.max_combo = int.from_bytes(self.replay_raw.read(2), byteorder="little")
        self.perfect = int.from_bytes(self.replay_raw.read(1), byteorder="little")
        self.mods = int.from_bytes(self.replay_raw.read(4), byteorder="little")
        self.lifebar = self.read_string()
        self.timestamp = int.from_bytes(self.replay_raw.read(8), byteorder="little")
        self.compressed_data_length = int.from_bytes(self.replay_raw.read(4), byteorder="little")
        self.data = self.replay_raw.read(self.compressed_data_length)
        self.online_play_id = int.from_bytes(self.replay_raw.read(8), byteorder="little")
        self.frames, self.frame_times = self.get_frames()

    def read_string(self):
        string_header = self.replay_raw.read(1)
        string = ""
        if string_header == b'\x0b':
            string_length = Uleb128(0).decode_from_stream(self.replay_raw, 'read', 1)
            string = self.replay_raw.read(string_length)

        return string

    def get_keys_from_bits(self, num: int):
        return [i for i in [1, 2, 4, 8, 16] if i & num]

    def get_frames(self):
        readable_data = lzma_decompress(self.data)
        replay_frames = readable_data.decode("utf-8").split(",")
        offset = int(replay_frames[1].split("|")[0])
        replay_frames = [frame.split("|") for frame in replay_frames[2:-2]]

        time = offset
        absolute_frames = []
        times = []
        for frame in replay_frames:
            time += int(frame[0])
            absolute_frames.append(
                Frame(time, int(frame[0]), float(frame[1]), float(frame[2]), self.get_keys_from_bits(int(frame[3]))))
            times.append(time)

        return absolute_frames, times
