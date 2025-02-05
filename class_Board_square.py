# ---------------------------------------------
# ------------ class Board_square -------------
# ---------------------------------------------

class Board_square():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, pos):
        self.pos = pos
        self.stones = [] # list of IDs which always has to be of length 1 or 0
        self.occupied = False # Is there a stone here?
        self.stone_properties = {} # [stone_ID] = [azimuth, ...]
        self.flags = {} # [flag_ID] = stone_ID

        self.causally_free_stones = [] # list of IDs of stones which are present and don't have a flag associated with them
        self.causally_locked_stones = {} # list of IDs of stones which have a flag associated with them - if the stone is added, it is not causally free. [flag_ID] = stone_ID

    def add_flag(self, new_flag_ID, new_stone_ID):
        self.flags[new_flag_ID] = new_stone_ID #TODO maybe order matters here?
        if new_stone_ID in self.causally_free_stones:
            self.causally_free_stones.remove(new_stone_ID)
        self.causally_locked_stones[new_flag_ID] = new_stone_ID

    def remove_flag(self, flag_ID):
        # Does the associated stone become causally free?
        associated_stone_ID = self.flags[flag_ID]
        if flag_ID in self.causally_locked_stones.keys():
            del self.causally_locked_stones[flag_ID]
        if associated_stone_ID in self.stones and associated_stone_ID not in self.causally_locked_stones.values():
            self.causally_free_stones.append(associated_stone_ID)
        del self.flags[flag_ID]

    def deactivate_flag(self, flag_ID):
        if flag_ID in self.causally_locked_stones.keys():
            del self.causally_locked_stones[flag_ID]
        if self.flags[flag_ID] in self.stones and self.flags[flag_ID] not in self.causally_locked_stones.values():
            self.causally_free_stones.append(self.flags[flag_ID])

    def activate_flag(self, flag_ID):
        self.causally_locked_stones[flag_ID] = self.flags[flag_ID]
        if self.flags[flag_ID] in self.causally_free_stones:
            self.causally_free_stones.remove(new_stone_ID)

    def remove_stones(self):
        self.stones = []
        self.occupied = False
        self.stone_properties = {}
        self.causally_free_stones = []
        # We do NOT clear causally_locked_stones, as this is just a descriptor of present flags

    def remove_stone(self, stone_ID):
        # Removes a specific stone if present
        if stone_ID in self.stones:
            self.stones.remove(stone_ID)
            del self.stone_properties[stone_ID]
        if stone_ID in self.causally_free_stones:
            self.causally_free_stones.remove(stone_ID)
        if len(self.stones) == 0:
            self.occupied = False

    def add_stone(self, new_stone_ID, new_stone_properties):
        # This function does allow for multiple stones to be here; but we expect the Gamemaster to resolve this before the display
        self.stones.append(new_stone_ID)
        self.stone_properties[new_stone_ID] = new_stone_properties.copy()
        if not new_stone_ID in self.causally_locked_stones.values():
            self.causally_free_stones.append(new_stone_ID)
        self.occupied = True
