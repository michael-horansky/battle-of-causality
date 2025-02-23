
import utils.functions as functions
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

from stones.class_Stone import Stone

# -----------------------------------------------------------------------------
# -------------------------------- class Mine ---------------------------------
# -----------------------------------------------------------------------------
# This is a neutral stone

class Mine(Stone):
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        super().__init__(stone_ID, progenitor_flag_ID, player_faction, t_dim)

        self.stone_type = "mine"

        self.opposable = True
        self.pushable = False
        self.orientable = False

        self.susceptible_to_own_explosion = True

    def reset_temporary_trackers(self):
        # SCR
        self.is_explosive_this_turn = True # always explosive
        # Tagscreen
        self.has_been_tag_locked = False
        self.has_been_tag_unlocked_this_turn = False
        self.unlock_tag_max_flag_ID_this_turn = None
        self.has_been_tag_hidden_this_turn = False

    def reset_temporary_time_specific_trackers(self):
        # SCR
        self.is_explosive_this_turn = True # Always explosive
        # Tagscreen
        self.has_been_tag_unlocked_this_turn = False
        self.unlock_tag_max_flag_ID_this_turn = None
        self.has_been_tag_hidden_this_turn = False


