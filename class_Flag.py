
import constants
from functions import *
from class_STPos import STPos

# -----------------------------------------------------------------------------
# -------------------------------- class Flag ---------------------------------
# -----------------------------------------------------------------------------
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

    # For tracking created stones
    max_stone_ID = 0
    @staticmethod
    def get_stone_ID_tag():
        new_tag = Flag.max_stone_ID
        Flag.max_stone_ID += 1
        return(new_tag)

    # For tracking flags
    max_flag_ID = 0
    @staticmethod
    def get_flag_ID_tag():
        new_tag = Flag.max_flag_ID
        Flag.max_flag_ID += 1
        return(new_tag)

    # ----------------------------------------------------
    # ------------------ class methods -------------------
    # ----------------------------------------------------

    @classmethod
    def from_str(cls, flag_representation):
        try:
            flag_elements = flag_representation.split(constants.Flag_delim)
            cur_flag_ID             =                int(flag_elements[0])
            cur_flag_type           =                    flag_elements[1]
            cur_flag_player_faction =                    flag_elements[2]
            cur_flag_stone_ID       =                int(flag_elements[3])
            cur_flag_pos            =     STPos.from_str(flag_elements[4])
            cur_flag_effect         = str_to_int_or_none(flag_elements[5])
            cur_flag_initial_cause  = str_to_int_or_none(flag_elements[6])
            cur_flag_args_list      =                    flag_elements[7:]
            if cur_flag_type == "add_stone":
                cur_flag_args = [cur_flag_args_list[0], int(cur_flag_args_list[1])]
            if cur_flag_type == "time_jump_out":
                cur_flag_args = [STPos.from_str(cur_flag_args_list[0])]
            if cur_flag_type == "time_jump_in":
                cur_flag_args = [cur_flag_args_list[0], int(cur_flag_args_list[1])]
            if cur_flag_type == "spatial_move":
                cur_flag_args = [int(cur_flag_args_list[0]), int(cur_flag_args_list[1]), int(cur_flag_args_list[2])]
            if cur_flag_type == "attack":
                cur_flag_args = cur_flag_args_list #[bool(cur_flag_args_list[0])]
            return(cls(pos = cur_flag_pos, flag_type = cur_flag_type, player_faction = cur_flag_player_faction, flag_args = cur_flag_args, stone_ID = cur_flag_stone_ID, flag_ID = cur_flag_ID, effect = cur_flag_effect, initial_cause = cur_flag_initial_cause))

        except:
            print(f"Flag(repr) attempted initialization from a badly formatted string representation: {flag_representation}")

    # ----------------------------------------------------
    # ------ constructors, destructors, descriptors ------
    # ----------------------------------------------------

    def __init__(self, pos, flag_type, player_faction, flag_args, stone_ID = -1, flag_ID = None, is_active = True, effect = None, initial_cause = None):
        self.pos = pos
        self.flag_type = flag_type
        self.player_faction = player_faction
        self.flag_args = flag_args.copy()
        self.stone_ID = stone_ID #-1 for anonymous flags, a non-negative integer otherwise
        if self.flag_type in Flag.stone_generating_flag_types:
            self.stone_ID = Flag.get_stone_ID_tag()

        # flag_ID is generated automatically if new Flag is being created, and
        # set to a specific value if an old Flag is being loaded into a new GM
        if flag_ID is None:
            self.flag_ID = Flag.get_flag_ID_tag()
        else:
            self.flag_ID = flag_ID
            Flag.max_flag_ID = max(Flag.max_flag_ID, self.flag_ID + 1)

        self.is_active = is_active
        self.effect = effect # If flag ID, the target flag requires this flag to activate to activate
        self.initial_cause = initial_cause # If this is a reverse effect, initial cause is always linked when buffered

    # NOTE: For flags subject to activity maps ('add_stone', 'time_jump_in'), the zeroth flag_arg is ALWAYS 'is_active'!
    # TODO: Make is_active a separate Flag property. Any flag can be deactivated. This is how we resolve deactivating flags
    # on the course off of which a stone has strayed by temporal tampering.
    def __str__(self):
        str_rep = 'UNDEFINED_MOVE'
        if self.flag_type == 'add_stone':
            # args: [stone_type, azimuth]
            str_rep = f"Add stone {self.flag_args[0].upper()} unconditionally (P. '{self.player_faction}', ID {self.stone_ID}): [{human_readable_azimuth(self.flag_args[1])}]"
            if self.is_active == False:
                str_rep += " (DEACTIVATED)"
        if self.flag_type == 'time_jump_out':
            # args: [STPos of time-jump-in]
            str_rep = f"Time jump OUT (P. '{self.player_faction}', ID {self.stone_ID}): jump into {self.flag_args[0]}"
        if self.flag_type == 'time_jump_in':
            # args: [stone_type, azimuth]
            str_rep = f"Stone {self.flag_args[0].upper()} time-jumps-IN (P. '{self.player_faction}', ID {self.stone_ID}): [{human_readable_azimuth(self.flag_args[1])}]"
            if self.is_active == False:
                str_rep += " (DEACTIVATED)"
        if self.flag_type == 'spatial_move':
            # args: [new_x, new_y, new_azimuth]
            str_rep = f"Spatial move (P. '{self.player_faction}', ID {self.stone_ID}): move to ({self.flag_args[0]},{self.flag_args[1]}) [{human_readable_azimuth(self.flag_args[2])}]"
        if self.flag_type == 'attack':
            # args: [allow_friendly_fire]
            str_rep = f"Attack (P. '{self.player_faction}', ID {self.stone_ID})"
            if self.flag_args[0]:
                str_rep += ": allows friendly fire"
            else:
                str_rep += ": forbids friendly fire"

        return(str_rep)
    def __repr__(self):
        return(self.__str__())

    def get_flag_representation(self):
        flag_representation = (constants.Flag_delim).join(str(x) for x in [self.flag_ID, self.flag_type, self.player_faction, self.stone_ID, self.pos, self.effect, self.initial_cause]) + (constants.Flag_delim)
        flag_representation += (constants.Flag_delim).join(str(x) for x in self.flag_args)
        return(flag_representation)

