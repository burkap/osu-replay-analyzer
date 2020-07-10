import os

from utils.analyzer import Analyzer
osu_path = "/insert/your/osu/path/here" # Ex: C:\Users<Username>\AppData\Local\osu!\
cwd = os.getcwd()
data_folder = os.path.join(cwd, "data")
replay_file = os.path.join(data_folder, "whitecat.osr")

an = Analyzer(replay_file, osu_path)

an.run()
