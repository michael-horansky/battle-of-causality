
# -----------------------------------------------------------------------------
# ---------------------------- class Board_square -----------------------------
# -----------------------------------------------------------------------------

class Board_square():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, pos):
        self.pos = pos
        self.stones = [] # list of IDs which has to be of length 1 or 0 for canonical boards
        self.occupied = False # Is there a stone here?
        self.stone_properties = {} # [stone_ID] = [azimuth, ...]

        self.flags = {None : []} # [stone_ID] = [flag 1, flag 2...]; [None] : [flags which happen even on unoccupied squares]
        self.all_flags = []

    def add_flag(self, new_flag_ID, required_actor):
        if required_actor not in self.flags.keys():
            self.flags[required_actor] = []
        self.flags[required_actor].append(new_flag_ID)
        self.all_flags.append(new_flag_ID)

    def remove_flag(self, flag_ID):
        for required_actor in self.flags.keys():
            if flag_ID in self.flags[required_actor]:
                self.flags[required_actor].remove(flag_ID)
        if flag_ID in self.all_flags:
            self.all_flags.remove(flag_ID)

    def remove_stones(self):
        self.stones = []
        self.occupied = False
        self.stone_properties = {}

    def remove_stone(self, stone_ID):
        # Removes a specific stone if present
        if stone_ID in self.stones:
            self.stones.remove(stone_ID)
            del self.stone_properties[stone_ID]
        if len(self.stones) == 0:
            self.occupied = False

    def add_stone(self, new_stone_ID, new_stone_properties):
        # This function does allow for multiple stones to be here; but we expect the Gamemaster to resolve this before the display
        self.stones.append(new_stone_ID)
        self.stone_properties[new_stone_ID] = new_stone_properties.copy()
        self.occupied = True
