class Frame:
    def __init__(self, time, time_since_previous, x, y, keys):
        self.time = time
        self.time_since_previous = time_since_previous
        self.x = x
        self.y = y

        self.m1_pressed = False
        self.m2_pressed = False
        self.k1_pressed = False
        self.k2_pressed = False
        self.smoke_pressed = False
        for i in keys:
            if i == 1:
                self.m1_pressed = True
            if i == 2:
                self.m2_pressed = True
            if i == 4:
                self.k1_pressed = True
            if i == 8:
                self.k2_pressed = True
            if i == 16:
                self.smoke_pressed = True