
import utils.functions as functions
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

from stones.class_Stone import Stone

# -----------------------------------------------------------------------------
# ------------------------------- class Tagger --------------------------------
# -----------------------------------------------------------------------------

class Tagger(Stone):
    delta_pos_list = [[1, 1, -2], [1, 2, -1], [1, 2, 1], [1, 1, 2], [1, -1, 2], [1, -2, 1], [1, -2, -1], [1, -1, -2], [0, 0, -2], [0, 2, 0], [0, 0, 2], [0, -2, 0], [-1, 0, -1], [-1, 1, 0], [-1, 0, 1], [-1, -1, 0]]
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        super().__init__(stone_ID, progenitor_flag_ID, player_faction, t_dim)

        self.stone_type = "tagger"

        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "jump/j" : ["x, y", "t, stone ID", "Jumps onto the specified square of distance 2 along one axis and distance 1 along another axis (including time, with delta_t = 0 if the next time-slice is targeted). The target time is determined automatically if not given! If stone ID specified, will swap the time-jump-in which generates said stone."],
                "tag/t" : ["type", None, "Deploys a tagscreen which affects this and all four adjanced squares. Type = \"lock\": affected stones become causally locked at the end of round. Type = \"unlock\": dispels effect of \"lock\" tagscreens applied to affected stones, or makes them causally free. Type = \"hide\": affected stones are forcefully teleported one time-slice forward (cannot be selected in the second-to-last timeslice)."]
                # NOTE: the unlock tagscreen doesn't actually force stones to become causallu free always, it just sets their max_flag_ID to this one's ID, overriding all flags placed in previous turns
            }

        self.type_specific_final_commands = {
                "pass" : [None, None, "No plag is placed, and this stone remains causally free. This is also selected on an empty submission!"],
                "jump/j" : ["x, y", "t, stone ID", "Jumps onto the specified square of distance 2 along one axis and distance 1 along another axis (including time). The target time is determined automatically if not given! If stone ID specified, will swap the time-jump-in which generates said stone."]
            }

        self.opposable = False
        self.orientable = False

    # -------------------------------------------------------------------------
    # -------------------------- Overridden methods ---------------------------
    # -------------------------------------------------------------------------

    def get_available_commands(self, gm):
        # Assumes the board is prepared in a proper way and that stone is
        # causally free in timeslice t corresponding to gm.current_turn_index.

        # This method returns a dictionary commands w/ the following structure:
        #   {
        #     "commands" : [list of command keys],
        #     "command_properties" : {
        #       "command key" : {
        #         "command_type" : name of command type as interpreted by Gamemaster,
        #         "selection_mode" : {
        #           "lock_timeslice" : t if SM is locked into a t.s., None otherwise,
        #           "squares" = [list of {
        #             "t", "x", "y",
        #             "a" : None or a list of available azimuths,
        #             "swap_effects" : a list of ante-effects which can be swapped here,
        #             "override_cmd_type" : if not None, this command type is used instead.
        #           } objects.]. If length is one, the first element is the default one.
        #           "choice_keyword": If not None, it's a string defining the key in the command dict,
        #           "choice_options" : "value",
        #           "choice_labels" : "label"
        #         },
        #         "label" : human-readable label
        #       }
        #     }
        #   }
        round_number, t = gm.round_from_turn(gm.current_turn_index)
        cur_x, cur_y, cur_a = self.history[t]
        available_commands = {"commands" : [], "command_properties" : {}}

        if t == gm.t_dim - 1:
            # Final time-slice

            # Command: pass
            available_commands["commands"].append("pass")
            available_commands["command_properties"]["pass"] = {
                    "command_type" : "pass",
                    "selection_mode" : {
                            "lock_timeslice" : gm.t_dim - 1,
                            "squares" : [{"t" : gm.t_dim - 1, "x" : cur_x, "y" : cur_y, "a" : None, "swap_effects" : None}],
                            "choice_keyword" : None,
                        },
                    "label" : "Pass"
                }

        else:
            # Other time-slices

            # Command: wait
            available_commands["commands"].append("wait")
            available_commands["command_properties"]["wait"] = {
                    "command_type" : "spatial_move",
                    "selection_mode" : {
                            "lock_timeslice" : None,
                            "squares" : [{"t" : t + 1, "x" : cur_x, "y" : cur_y, "a" : None, "swap_effects" : None}],
                            "choice_keyword" : None
                        },
                    "label" : "Wait"
                }


            # Command: tag
            available_tag_options = ["lock", "unlock"]
            available_tag_labels = ["Causal lock", "Causal unlock"]
            if t < gm.t_dim - 2:
                available_tag_options.append("hide")
                available_tag_labels.append("Smokescreen")
            available_commands["commands"].append("tag")
            available_commands["command_properties"]["tag"] = {
                    "command_type" : "tag",
                    "selection_mode" : {
                            "lock_timeslice" : t + 1,
                            "squares" : [{"t" : t + 1, "x" : cur_x, "y" : cur_y, "a" : None, "swap_effects" : None}],
                            "choice_keyword" : "tag_type",
                            "choice_options" : available_tag_options,
                            "choice_labels" : available_tag_labels
                        },
                    "label" : "Tag"
                }

        # Command: jump
        available_jump_squares = []
        # First we check the 8 horse-move jumps
        for delta_pos in Tagger.delta_pos_list:
            target_t = t + delta_pos[0]
            target_x = cur_x + delta_pos[1]
            target_y = cur_y + delta_pos[2]
            if 0 <= target_t and target_t < gm.t_dim and gm.is_square_available(target_x, target_y):
                new_square_element = {"t" : target_t, "x" : target_x, "y" : target_y, "a" : None, "swap_effects" : None}
                if delta_pos[0] <= 0:
                    new_square_element["override_cmd_type"] = "timejump"
                    new_square_element["swap_effects"] = [None] + self.get_available_timejump_swaps(gm, round_number, target_t, target_x, target_y)
                available_jump_squares.append(new_square_element)
        if len(available_jump_squares) > 0:
            available_commands["commands"].append("jump")
            available_commands["command_properties"]["jump"] = {
                    "command_type" : "spatial_move",
                    "selection_mode" : {
                            "lock_timeslice" : None,
                            "squares" : available_jump_squares,
                            "choice_keyword" : None,
                        },
                    "label" : "Jump"
                }


        return(available_commands)

    # ---------------- LEGACY FEATURE: LOCAL TUI COMPATIBILITY ----------------
    # ------------------------ Command parsing methods ------------------------

    def parse_move_cmd(self, gm):

        # This makes gamemaster add new moves based on the player input and the unique properties of the stone
        # it is called in the game_loop functions
        # this is the method you change when inheriting Stone

        # Default controls: tanks

        # This method must return a Message
        round_number, t = gm.round_from_turn(gm.current_turn_index)
        cur_x, cur_y, cur_a = self.history[t]
        while(True):
            try:
                input_cmd_raw = input("Input the command in the form \"[command name] [argument]\", or type \"help\": ")
                input_cmd_raw = input_cmd_raw.rstrip(" ").lstrip(" ")

                # Generic commands
                generic_msg = self.parse_generic_move_cmd(gm, input_cmd_raw, cur_x, cur_y)
                if generic_msg.header == "continue":
                    continue
                elif generic_msg.header == "exception":
                    raise Exception(generic_msg.msg)
                elif generic_msg.header == "option":
                    return(generic_msg) # The Gamemaster handles options!


                if input_cmd_raw in ['', 'w', 'wait']:
                    return(Message("command", {"type" : "spatial_move", "new_x" : cur_x, "new_y" : cur_y, "new_a" : cur_a}))

                # From now on, we need to consider the command arguments

                input_cmd_list = input_cmd_raw.split(' ')

                if input_cmd_list[0] in ['j', 'jump']:
                    if len(input_cmd_list) not in [3, 4, 5]:
                        raise Exception("Required arguments missing")
                    new_x = int(input_cmd_list[1])
                    new_y = int(input_cmd_list[2])
                    spatial_distances = set([abs(new_x - cur_x), abs(new_y - cur_y)])
                    if spatial_distances == set([1, 2]):
                        new_t = t + 1
                    elif spatial_distances == set([0, 2]):
                        new_t = t
                    elif spatial_distances == set([1, 0]):
                        new_t = t - 1
                    else:
                        raise Exception("Selected spatial position invalid")

                    if len(input_cmd_list) == 4:
                        if int(input_cmd_list[3]) != new_t:
                            raise Exception("Target time invalid with selected spatial position")

                    if new_t < 0:
                        raise Exception("Lowest target time value is 0")
                    if new_t >= gm.t_dim:
                        raise Exception(f"Largest target time value is {gm.t_dim - 1}")

                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Target spatial position not available")

                    if new_t == t + 1:
                        # We cannot swap a forward move! Just follow the old version bruv
                        return(Message("command", {"type" : "spatial_move", "new_x" : new_x, "new_y" : new_y, "new_a" : 0}))
                    else:
                        # This is a timejump, and we need to check if the stone is tag locked
                        if self.has_been_tag_locked:
                            raise Exception("This stone has been tag locked, and thus cannot perform a new time-jump-out.")
                        # Check if swapping
                        if len(input_cmd_list) == 5:
                            adopted_stone_ID = int(input_cmd_list[4])
                            # Is stone correct?
                            if adopted_stone_ID not in gm.stones:
                                raise Exception("Stone ID invalid")
                            adopted_stone_progenitor = gm.stones[adopted_stone_ID].progenitor_flag_ID
                            if gm.flags[adopted_stone_progenitor].flag_type != "time_jump_in":
                                raise Exception("Specified stone is not placed onto the board via a time-jump-in")
                            if not (gm.flags[adopted_stone_progenitor].pos.t == new_t - 1 and gm.flags[adopted_stone_progenitor].pos.x == new_x and gm.flags[adopted_stone_progenitor].pos.y == new_y):
                                raise Exception("Specified stone doesn't time-jump-in at the specified square")
                            if self.player_faction != gm.stones[adopted_stone_ID].player_faction:
                                raise Exception("Specified stone belongs to a different faction")
                            if self.stone_type not in [gm.stones[adopted_stone_ID].stone_type, "wildcard"]:
                                raise Exception("Specified stone is of incompatible type")
                            if gm.stones[adopted_stone_ID].orientable and gm.flags[adopted_stone_progenitor].flag_args[1] != new_a:
                                raise Exception("Specified stone jumps in at a different azimuth than proposed")

                            for TJI_ID in gm.effects_by_round[round_number]:
                                if TJI_ID == adopted_stone_progenitor:
                                    raise Exception("Specified time-jump-in has been added only this round, and thus hasn't been realised yet.")

                            return(Message("command", {"type" : "timejump", "new_t" : new_t, "new_x" : new_x, "new_y" : new_y, "new_a" : 0, "adopted_stone_ID" : adopted_stone_ID}))

                        else:
                            # not swapping
                            return(Message("command", {"type" : "timejump", "new_t" : new_t, "new_x" : new_x, "new_y" : new_y, "new_a" : 0}))

                if input_cmd_list[0] in ['t', 'tag']:
                    if len(input_cmd_list) != 2:
                        raise Exception("Required argument missing")
                    tag_type = input_cmd_list[1]
                    if tag_type not in ["lock", "unlock", "hide"]:
                        raise Exception("Tagscreen type not recognised")
                    if tag_type == "hide" and t >= gm.t_dim - 2:
                        raise Exception("The \"hide\" tagscreen cannot be selected on the second-to-last time-slice")

                    return(Message("command", {"type" : "tag", "tag_type" : tag_type}))
                raise Exception("Your input couldn't be parsed")

            except Exception as e:
                print("Try again;", e)

    def parse_final_move_cmd(self, gm):

        # Just the same as parse_move_cmd, except this one is called in the final time-slice. Here, the stones
        # can either pass (if their type allows it), which leaves them causally free so that they can jump back
        # in the next rounds, or they can do a time-jump-out (or some other type-specific action which affects
        # the previous time-slices, not the future ones).
        round_number, t = gm.round_from_turn(gm.current_turn_index)
        cur_x, cur_y, cur_a = self.history[t]
        while(True):
            try:
                input_cmd_raw = input("Input the command in the form \"[command name] [argument]\", or type \"help\": ")
                input_cmd_raw = input_cmd_raw.rstrip(" ").lstrip(" ")

                # Generic commands
                generic_msg = self.parse_generic_move_cmd(gm, input_cmd_raw, cur_x, cur_y, is_final_command = True)
                if generic_msg.header == "continue":
                    continue
                elif generic_msg.header == "exception":
                    raise Exception(generic_msg.msg)
                elif generic_msg.header == "option":
                    return(generic_msg) # The Gamemaster handles options!


                if input_cmd_raw in ['', 'p', 'pass']:
                    return(Message("pass"))

                # From now on, we need to consider the command arguments

                input_cmd_list = input_cmd_raw.split(' ')

                if input_cmd_list[0] in ['j', 'jump']:
                    if len(input_cmd_list) not in [3, 4, 5]:
                        raise Exception("Required arguments missing")
                    new_x = int(input_cmd_list[1])
                    new_y = int(input_cmd_list[2])
                    spatial_distances = set([abs(new_x - cur_x), abs(new_y - cur_y)])
                    if spatial_distances == set([1, 2]):
                        new_t = t + 1
                    elif spatial_distances == set([0, 2]):
                        new_t = t
                    elif spatial_distances == set([1, 0]):
                        new_t = t - 1
                    else:
                        raise Exception("Selected spatial position invalid")

                    if len(input_cmd_list) == 4:
                        if int(input_cmd_list[3]) != new_t:
                            raise Exception("Target time invalid with selected spatial position")

                    if new_t < 0:
                        raise Exception("Lowest target time value is 0")
                    if new_t >= gm.t_dim:
                        raise Exception(f"Largest target time value is {gm.t_dim - 1}")

                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Target spatial position not available")

                    if new_t == t + 1:
                        # We cannot swap a forward move! Just follow the old version bruv
                        return(Message("command", {"type" : "spatial_move", "new_x" : new_x, "new_y" : new_y, "new_a" : 0}))
                    else:
                        # This is a timejump, and we need to check if the stone is tag locked
                        if self.has_been_tag_locked:
                            raise Exception("This stone has been tag locked, and thus cannot perform a new time-jump-out.")
                        # Check if swapping
                        if len(input_cmd_list) == 5:
                            adopted_stone_ID = int(input_cmd_list[4])
                            # Is stone correct?
                            if adopted_stone_ID not in gm.stones:
                                raise Exception("Stone ID invalid")
                            adopted_stone_progenitor = gm.stones[adopted_stone_ID].progenitor_flag_ID
                            if gm.flags[adopted_stone_progenitor].flag_type != "time_jump_in":
                                raise Exception("Specified stone is not placed onto the board via a time-jump-in")
                            if not (gm.flags[adopted_stone_progenitor].pos.t == new_t - 1 and gm.flags[adopted_stone_progenitor].pos.x == new_x and gm.flags[adopted_stone_progenitor].pos.y == new_y):
                                raise Exception("Specified stone doesn't time-jump-in at the specified square")
                            if self.player_faction != gm.stones[adopted_stone_ID].player_faction:
                                raise Exception("Specified stone belongs to a different faction")
                            if self.stone_type not in [gm.stones[adopted_stone_ID].stone_type, "wildcard"]:
                                raise Exception("Specified stone is of incompatible type")
                            if gm.stones[adopted_stone_ID].orientable and gm.flags[adopted_stone_progenitor].flag_args[1] != new_a:
                                raise Exception("Specified stone jumps in at a different azimuth than proposed")

                            for TJI_ID in gm.effects_by_round[round_number]:
                                if TJI_ID == adopted_stone_progenitor:
                                    raise Exception("Specified time-jump-in has been added only this round, and thus hasn't been realised yet.")

                            return(Message("command", {"type" : "timejump", "new_t" : new_t, "new_x" : new_x, "new_y" : new_y, "new_a" : 0, "adopted_stone_ID" : adopted_stone_ID}))

                        else:
                            # not swapping
                            return(Message("command", {"type" : "timejump", "new_t" : new_t, "new_x" : new_x, "new_y" : new_y, "new_a" : 0}))

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)


