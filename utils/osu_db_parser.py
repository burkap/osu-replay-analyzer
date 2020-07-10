from typing import Union
from io import BytesIO
from utils.leb128 import Uleb128
from lzma import decompress as lzma_decompress
from utils.frame import Frame


class DatabaseParser:
    def __init__(self, database_file: Union[str, BytesIO]):
        if isinstance(database_file, str):
            with open(database_file, "rb") as replay:
                self.database_raw = BytesIO(replay.read())
        else:
            self.database_raw = database_file

        self.beatmaps = dict()
        self.database_raw.seek(0)
        self.version = int.from_bytes(self.database_raw.read(4), byteorder="little")
        self.folder_count = int.from_bytes(self.database_raw.read(4), byteorder="little")
        self.account_unlocked = int.from_bytes(self.database_raw.read(1), byteorder="little")
        self.date_time = int.from_bytes(self.database_raw.read(8), byteorder="little")
        self.username = self.read_string()
        self.beatmap_count = int.from_bytes(self.database_raw.read(4), byteorder="little")
        for _ in range(self.beatmap_count):
            self.beatmaps.update(self.read_beatmap())

    def read_beatmap(self):
        if int(self.version) < 20191106:
            int.from_bytes(self.database_raw.read(4), byteorder="little")
        artist_name = self.read_string()
        artist_name_u = self.read_string()
        song_title = self.read_string()
        song_title_u = self.read_string()
        creator_name = self.read_string()
        difficulty = self.read_string()
        audio_file = self.read_string()
        md5hash = self.read_string()
        osu_file = self.read_string()
        ###############
        # Discarding down below
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(2), byteorder="little")
        int.from_bytes(self.database_raw.read(2), byteorder="little")
        int.from_bytes(self.database_raw.read(2), byteorder="little")
        int.from_bytes(self.database_raw.read(8), byteorder="little")
        if int(self.version) < 20140609:
            int.from_bytes(self.database_raw.read(1), byteorder="little")
            int.from_bytes(self.database_raw.read(1), byteorder="little")
            int.from_bytes(self.database_raw.read(1), byteorder="little")
            int.from_bytes(self.database_raw.read(1), byteorder="little")
        else:
            int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(4), byteorder="little")

        int.from_bytes(self.database_raw.read(8), byteorder="little")

        if int(self.version) > 20140609:
            std_count = int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(14*std_count), byteorder="little")
            std_count = int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(14*std_count), byteorder="little")
            std_count = int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(14*std_count), byteorder="little")
            std_count = int.from_bytes(self.database_raw.read(4), byteorder="little")
            int.from_bytes(self.database_raw.read(14*std_count), byteorder="little")

        int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(4), byteorder="little")

        timing_points = int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(17*timing_points), byteorder="little")

        int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(4), byteorder="little")

        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")

        int.from_bytes(self.database_raw.read(2), byteorder="little")
        int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")

        song_source = self.read_string()
        song_tags = self.read_string()

        int.from_bytes(self.database_raw.read(2), byteorder="little")
        self.read_string()
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(8), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        rel = self.read_string()
        int.from_bytes(self.database_raw.read(8), byteorder="little")

        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")

        if int(self.version) < 20140609:
            int.from_bytes(self.database_raw.read(2), byteorder="little")
        int.from_bytes(self.database_raw.read(4), byteorder="little")
        int.from_bytes(self.database_raw.read(1), byteorder="little")
        ###############
        #print(md5hash)
        return {md5hash.decode('UTF-8'): (rel.decode('UTF-8'), audio_file.decode('UTF-8'), osu_file.decode('UTF-8'))}

    def read_string(self):
        string_header = self.database_raw.read(1)
        string = b''
        if string_header == b'\x0b':
            string_length = Uleb128(0).decode_from_stream(self.database_raw, 'read', 1)
            string = self.database_raw.read(string_length)

        return string
