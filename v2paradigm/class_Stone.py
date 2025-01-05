
from functions import *

# ---------------------------------------------
# ---------------- class Stone ----------------
# ---------------------------------------------

class Stone():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, player_faction):

        self.ID = stone_ID
        self.player_faction = player_faction


        self.events = {'death':[], 'time_jump':[]} #keeps track of whether the stone is causally free
        self.causal_freedom_time = 1 # if it spawns into t, it can be moved from t+1

        # maybe also remember position and azimuth at cft?
