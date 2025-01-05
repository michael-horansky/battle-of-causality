

from functions import *

# ---------------------------------------------
# ---------------- class Flag -----------------
# ---------------------------------------------
# Instances of this class are commands associated with a specific spacetime position.
# The only interface between the board and the players is the adding of flags to board squares.
# A flag has a type which specifies what action it represents.
# The type of a flag also specifies whether it is tied to a specific stone ID or anonymous.
# (For example, a spatial move is tied to an ID, so if a different stone occupies the square, it will not move.
# But time jumps are anonymous, as any stone of the right faction can step in and travel back to fill the same shoes.)

class Flag():

    # ----------------------------------------------------
    # ------------------ static methods ------------------
    # ----------------------------------------------------

    # The following is used to generate IDs for Flags which create new stones.
    # These flags are not anonymous, but are not provided with an ID, as it doesn't exist yet.
    stone_generating_flag_types = ['add_stone', 'time_jump_in']
    max_ID = 0
    @staticmethod
    def get_ID_tag():
        new_tag = Flag.max_ID
        Flag.max_ID += 1
        return(new_tag)

    # ----------------------------------------------------
    # ------ constructors, destructors, descriptors ------
    # ----------------------------------------------------

    def __init__(self, flag_type, player_faction, flag_args, stone_ID = -1):
        self.flag_type = flag_type
        self.player_faction = player_faction
        self.flag_args = flag_args.copy()
        self.stone_ID = stone_ID #-1 for anonymous flags, a non-negative integer otherwise
        if self.flag_type in Flag.stone_generating_flag_types:
            self.stone_ID = Flag.get_ID_tag()

    def __str__(self):
        str_rep = 'UNDEFINED_MOVE'
        if self.flag_type == 'add_stone':
            str_rep = f"Add stone unconditionally (P. '{self.player_faction}', ID {self.stone_ID}): [{human_readable_azimuth(self.flag_args[0])}]"
        if self.flag_type == 'time_jump_out':
            str_rep = f"Time jump OUT (P. '{self.player_faction}', ID {self.stone_ID}): jump into {self.flag_args[0]}"
        if self.flag_type == 'time_jump_in':
            str_rep = f"Time jump IN (P. '{self.player_faction}', ID {self.stone_ID}): t = {self.flag_args[1]}"
        if self.flag_type == 'spatial_move':
            str_rep = f"Spatial move (P. '{self.player_faction}', ID {self.stone_ID}): move to {self.flag_args[0]} [{human_readable_azimuth(self.flag_args[1])}]"
        if self.flag_type == 'attack':
            str_rep = f"Attack (P. '{self.player_faction}', ID {self.stone_ID})"

        return(str_rep)
    def __repr__(self):
        return(self.__str__())

