
from functions import *

class stone():
    
    def __init__(self, my_pos_x_0, my_pos_y_0, my_orientation, my_parent = None, my_child = None):
        
        self.pos_x_0 = my_pos_x_0
        self.pos_y_0 = my_pos_y_0
        
        self.a_0 = my_orientation #0 = up, 1 = right, 2 = down, 3 = left; a for azimuth
        
        self.moves = []
        
        # 'position' = (x, y), acts as a primary key together with t (indistinguishable particles)
        
        self.position = [(self.pos_x_0, self.pos_y_0)] #[time: (x, y)]
        self.azimuth = [self.a_0]
        
        self.parent = my_parent
        self.child  = my_child
    
    def __str__(self):
        return("Stone; x_0=%i, y_0=%i" % (self.pos_x_0, self.pos_y_0))
    def __repr__(self):
        return("Stone; x_0=%i, y_0=%i" % (self.pos_x_0, self.pos_y_0))
    
    def reset_stone(self):
        if self.parent == None:
            self.position = [(self.pos_x_0, self.pos_y_0)] #[time: (x, y)]
            self.azimuth = [self.a_0]
            return('original')
        else:
            self.position = []
            self.azimuth = []
            return('child')
    
    def get_position(self, t=-1):
        if t == -1 or (t >= 0 and t < len(self.position)):
            return(self.position[t])
        return(-1)
    
    def get_azimuth(self, t=-1):
        if t == -1 or (t >= 0 and t < len(self.azimuth)):
            return(self.azimuth[t])
        return(-1)
        
    def move(self, cmd):
        
        # add move to self.moves
        print("stone.move")

class stone_line():
    
    def __init__(self, ancestor_stone):
        
        self.stones = [ancestor_stone]
