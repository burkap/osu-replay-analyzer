import os
from sys import platform
from utils.analyzer import Analyzer
if platform == "win32":
    from utils.config_parser import osu_path
else:
    osu_path = "/insert/your/osu/path/here" # Ex: C:\Users<Username>\AppData\Local\osu!\

cwd = os.getcwd()
data_folder = os.path.join(cwd, "data")
replay_file = os.path.join(data_folder, "whitecat.osr")

an = Analyzer(replay_file, osu_path)

an.run()
