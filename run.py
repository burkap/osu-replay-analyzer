import os

from utils.analyzer import Analyzer

cwd = os.getcwd()
data_folder = os.path.join(cwd, "data")
replay_file = os.path.join(data_folder, "whitecat.osr")
bmap_file = os.path.join(data_folder, "whitecat.osu")
an = Analyzer(replay_file, bmap_file)

an.analyze_for_relax()