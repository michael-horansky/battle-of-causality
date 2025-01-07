
from functions import *

# ---------------------------------------------
# ---------------- class Stone ----------------
# ---------------------------------------------

class Stone():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, player_faction, t_dim):

        self.ID = stone_ID
        self.player_faction = player_faction


        self.events = {'death':[], 'time_jump':[]} #keeps track of whether the stone is causally free
        self.causal_freedom_time = 0 # if it spawns into t, it can be moved from t

        self.history = [None] * t_dim # This allows the stone to remember its positions in time, shortening tracking time. [t] = (x,y,a)

        # maybe also remember position and azimuth at cft?
