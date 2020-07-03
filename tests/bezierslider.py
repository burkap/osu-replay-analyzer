import pygame
from utils.mathhelper import Vec2

from utils.gui import GUI, Hitobject_Slider, Hitcircle

gui = GUI(600, 300)

control_points = [Vec2(100, 100), Vec2(200, 200),
                  Vec2(300, 100), Vec2(400, 200), Vec2(500, 100)]


#hc1 = Hitcircle(control_points[0].x, control_points[0].y)

#hc1 = Hitcircle(control_points[-1].x, control_points[-1].y)
slider = Hitobject_Slider(control_points, 31, True)

selected = None
while True:
    slider.set_control_points(control_points)
    if gui.is_holding_down:
        for p in control_points:
            if p.distance(Vec2(gui.mouse[0], gui.mouse[1])) < 31:
                selected = p
    else:
        selected = None

    if selected is not None:
        selected.x, selected.y = gui.mouse

    gui.draw()
