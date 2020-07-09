import os

from utils.analyzer import Analyzer

cwd = os.getcwd()
data_folder = os.path.join(cwd, "data")
replay_file = os.path.join(data_folder, "ronald.osr")
bmap_file = os.path.join(data_folder, "lady.osu")
an = Analyzer(replay_file, bmap_file)

an.run()
