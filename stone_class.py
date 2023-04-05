
from functions import *

class Stone():
    
    def __init__(self, stone_ID, round_number, player_faction, pos_0, a_0, my_parent = None, my_child = None):
        
        self.ID = stone_ID
        self.round_number = round_number #which round was this stone created in - useful for causal freedom analysis
        self.player_faction = player_faction
        #my_pos_x_0, my_pos_y_0 = my_pos_0
        #self.pos_x_0 = my_pos_x_0
        #self.pos_y_0 = my_pos_y_0
        
        #self.a_0 = my_orientation #0 = up, 1 = right, 2 = down, 3 = left; a for azimuth
        
        self.events = {'death':[], 'time_jump':[]} #keeps track of whether the stone is causally free
        self.causal_freedom_time = len(pos_0) # if it spawns into t, it can be moved from t+1
        
        # 'position' = (x, y), acts as a primary key together with t (indistinguishable particles)
        
        if type(pos_0) != list:
            pos_0 = [pos_0]
        if type(a_0  ) != list:
            a_0   = [a_0]
        
        self.position = pos_0.copy()#[(self.pos_x_0, self.pos_y_0)] #[time: (x, y)]
        self.azimuth = a_0.copy()#[self.a_0]
        
        self.parent = my_parent
        self.child  = my_child
    
    def __str__(self):
        return(f"Stone; pos = {self.position}, a = {self.azimuth}")
        #return("Stone; x_0=%i, y_0=%i" % (self.pos_x_0, self.pos_y_0))
    def __repr__(self):
        return(f"Stone; pos = {self.position}, a = {self.azimuth}")
        #return("Stone; x_0=%i, y_0=%i" % (self.pos_x_0, self.pos_y_0))
    
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
    
    def is_causally_free(self, t):
        # is causally free IF it doesn't link to another position AND is linked to no events (if despawn event occured before, the stone is despawned. if it occured after, it's causally dependent)
        print(f"checking {t} against {self.causal_freedom_time}")
        for key, item in self.events.items():
            if len(item) > 0:
                result = False
        if self.causal_freedom_time == t:
            return(True)
        return(False)
        """result = False
        if self.get_position(t) != -1 and self.get_position(t+1) == -1:
            result = True
        for key, item in self.events.items():
            if len(item) > 0:
                result = False
        return(result)"""
    def progress_causal_freedom(self, t, T, causing_round_number):
        if causing_round_number < self.round_number:
            return(-1) #not affected
        # this means an event happened at t which progressed the causal freedom to t+1 for all stones that were causally free at t
        if self.causal_freedom_time == t:
            self.causal_freedom_time += 1
        if self.causal_freedom_time >= T:
            self.causal_freedom_time = -1
        
    def move(self, cmd):
        
        # add move to self.moves
        print("stone.move")

class stone_line():
    
    def __init__(self, ancestor_stone):
        
        self.stones = [ancestor_stone]
