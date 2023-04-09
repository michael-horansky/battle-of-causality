
from functions import *

class Stone():
    
    def __init__(self, stone_ID, round_number, player_faction, pos_0, a_0):
        
        self.ID = stone_ID
        self.round_number = round_number #which round was this stone created in - useful for causal freedom analysis
        self.player_faction = player_faction
        #my_pos_x_0, my_pos_y_0 = my_pos_0
        #self.pos_x_0 = my_pos_x_0
        #self.pos_y_0 = my_pos_y_0
        
        #self.a_0 = my_orientation #0 = up, 1 = right, 2 = down, 3 = left; a for azimuth
        
        self.events = {'death':[], 'time_jump':[]} #keeps track of whether the stone is causally free
        self.causal_freedom_time = len(pos_0) # if it spawns into t, it can be moved from t+1
        
        # 'position' = (x, y)
        
        if type(pos_0) != list:
            pos_0 = [pos_0]
        if type(a_0  ) != list:
            a_0   = [a_0]
        
        self.position = pos_0.copy()#[(self.pos_x_0, self.pos_y_0)] #[time: (x, y)]
        self.azimuth = a_0.copy()#[self.a_0]
    
    def __str__(self):
        return(f"Stone; pos = {self.position}, a = {self.azimuth}")
        #return("Stone; x_0=%i, y_0=%i" % (self.pos_x_0, self.pos_y_0))
    def __repr__(self):
        return(f"Stone; pos = {self.position}, a = {self.azimuth}")
        #return("Stone; x_0=%i, y_0=%i" % (self.pos_x_0, self.pos_y_0))
    
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
        for key, item in self.events.items():
            if len(item) > 0:
                return(False)
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
        
    def parse_move_cmd(self, gm, t):
        
        # This makes gamemaster add new moves based on the player input and the unique properties of the stone
        # it is called in the game_loop functions
        # this is the method you change when inheriting Stone
        
        # Default controls: tanks
        while(True):
            try:
                input_cmd_raw = input("  Input the command in the form \"fwd/bwd/turn/atk [arguments]\": ")
                if input_cmd_raw in ['u', 'undo', 'unselect']:
                    print("  Unselecting stone...")
                    return(-1)
                
                input_cmd_list = input_cmd_raw.split(' ')
                
                pos0 = self.get_position(t)
                a0 = self.get_azimuth(t)
                
                added_move_msg = 0
                
                if input_cmd_list[0] in ['f', 'fwd', 'forward']:
                    if len(input_cmd_list) <= 1:
                        a1 = a0
                    else:
                        a1 = int(input_cmd_list[1])
                    if np.abs(a0 - a1) == 2: #U-turn
                        print("  This stone can't make a U-turn whilst traversing the board.")
                        return(-1)
                    pos1 = pos_step(pos0, a0)
                    added_move_msg = gm.add_spatial_move(t, pos0, pos1, a1, self.player_faction)
                elif input_cmd_list[0] in ['b', 'bwd', 'backward']:
                    if len(input_cmd_list) <= 1:
                        a1 = a0
                    else:
                        a1 = int(input_cmd_list[1])
                    if np.abs(a0 - a1) == 2: #U-turn
                        print("  This stone can't make a U-turn whilst traversing the board.")
                        return(-1)
                    pos1 = pos_step(pos0, azimuth_addition(a0, 2))
                    added_move_msg = gm.add_spatial_move(t, pos0, pos1, a1, self.player_faction)
                elif input_cmd_list[0] in ['t', 'turn']:
                    if len(input_cmd_list) <= 1:
                        a1 = a0
                    else:
                        a1 = int(input_cmd_list[1])
                    pos1 = pos0
                    added_move_msg = gm.add_spatial_move(t, pos0, pos1, a1, self.player_faction)
                elif input_cmd_list[0] in ['a', 'atk', 'attack']:
                    added_move_msg = gm.add_attack(t, self, allow_friendly_fire = True)
                
                return(added_move_msg)
                
            except:
                print("Your input couldn't be parsed")
        

class StoneTank(Stone):
    
    
    # A type of stone that can move using tank controls and then fire in the same move
    
    def __init__(self, stone_ID, round_number, player_faction, pos_0, a_0):
        super().__init__(stone_ID, round_number, player_faction, pos_0, a_0)
    
    
