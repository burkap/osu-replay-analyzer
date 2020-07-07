from utils.gui import GUI, Hitcircle, Cursor

gui = GUI(512, 384)
hc = Hitcircle(50, 60, 31)
trail = Cursor((150, 70), [(10, 10), (20, 25), (150, 70)])
while 1:
    gui.draw()
