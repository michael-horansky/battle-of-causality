
import utils.functions as functions
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

from stones.class_Stone import Stone

# -----------------------------------------------------------------------------
# -------------------------------- class Tank ---------------------------------
# -----------------------------------------------------------------------------

class Tank(Stone):
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        super().__init__(stone_ID, progenitor_flag_ID, player_faction, t_dim)

        self.stone_type = "tank"

        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "forward/fwd" : [None, "turn", "Moves forward by 1, turning clockwise/cw or anticlockwise/acw by 90 deg. if specified."],
                "backward/bwd" : [None, "turn", "Moves backward by 1, turning clockwise/cw or anticlockwise/acw by 90 deg. if specified."],
                "turn/t" : ["azimuth", None, "Faces the specified direction (up/right/down/left)."],
                "attack/atk" : [None, None, "Fires, destroying the stone in line of sight."]
            }

        self.type_specific_final_commands = {
                "pass" : [None, None, "No plag is placed, and this stone remains causally free. This is also selected on an empty submission!"],
                "timejump/tj" : ["time", "stone ID", "Jumps back into the specified time (spatial position unchanged). If stone ID specified, will swap the time-jump-in which generates said stone."]
            }

        self.opposable = True
        self.orientable = True

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
        #           "is_required" : True or False,
        #           "lock_timeslice" : t if SM is locked into a t.s., None otherwise,
        #           "squares" = [list of {
        #             "t", "x", "y",
        #             "a" : None or a list of available azimuths,
        #             "swap_effects" : a list of ante-effects which can be swapped here. Can be empty.
        #           } objects.]. If length is one, the first element is the default one.
        #         },
        #         "azimuths" : None if azimuth argument not required or provided by selecion mode, a list of available azimuths otherwise,
        #         "choice_keyword": If not None, it's a string defining the key in the command dict,
        #         "choice_options" : [list of values the user can pick from],
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
                    "selection_mode" : {"is_required" : False},
                    "azimuths" : None,
                    "choice_keyword" : None,
                    "label" : "Pass"
                }

            # Command: timejump
            available_timejump_squares = self.get_available_timejumps(gm, round_number, t, cur_x, cur_y, cur_a)
            if len(available_timejump_squares) > 0:
                available_commands["commands"].append("timejump")
                available_commands["command_properties"]["timejump"] = {
                        "command_type" : "timejump",
                        "selection_mode" : {
                                "is_required" : True,
                                "lock_timeslice" : None,
                                "squares" : available_timejump_squares
                            },
                        "azimuths" : None,
                        "choice_keyword" : None,
                        "label" : "Timejump"
                    }
        else:
            # Other time-slices

            # Command: wait
            available_commands["commands"].append("wait")
            available_commands["command_properties"]["wait"] = {
                    "command_type" : "spatial_move",
                    "selection_mode" : {
                            "is_required" : True,
                            "lock_timeslice" : None,
                            "squares" : [{"t" : t + 1, "x" : cur_x, "y" : cur_y, "a" : [cur_a], "swap_effects" : None}]
                        },
                    "azimuths" : None,
                    "choice_keyword" : None,
                    "label" : "Wait"
                }

            # Command: turn
            available_commands["commands"].append("turn")
            available_commands["command_properties"]["turn"] = {
                    "command_type" : "spatial_move",
                    "selection_mode" : {
                            "is_required" : True,
                            "lock_timeslice" : None,
                            "squares" : [{"t" : t + 1, "x" : cur_x, "y" : cur_y, "a" : [0, 1, 2, 3], "swap_effects" : None}]
                        },
                    "azimuths" : [0, 1, 2, 3],
                    "choice_keyword" : None,
                    "label" : "Turn"
                }

            # Command: move

            available_move_squares = []
            fwd_x, fwd_y = functions.pos_step((cur_x, cur_y), cur_a)
            bwd_x, bwd_y = functions.pos_step((cur_x, cur_y), functions.azimuth_addition(cur_a, 2))
            tank_azimuths = [cur_a, functions.azimuth_addition(cur_a, 1), functions.azimuth_addition(cur_a, -1)]
            if gm.is_square_available(fwd_x, fwd_y):
                available_move_squares.append({"t" : t+1, "x" : fwd_x, "y" : fwd_y, "a" : tank_azimuths, "swap_effects" : None})
            if gm.is_square_available(bwd_x, bwd_y):
                available_move_squares.append({"t" : t+1, "x" : bwd_x, "y" : bwd_y, "a" : tank_azimuths, "swap_effects" : None})

            if len(available_move_squares) > 0:
                available_commands["commands"].append("move")
                available_commands["command_properties"]["move"] = {
                        "command_type" : "spatial_move",
                        "selection_mode" : {
                                "is_required" : True,
                                "lock_timeslice" : t + 1,
                                "squares" : available_move_squares
                            },
                        "azimuths" : None,
                        "choice_keyword" : None,
                        "label" : "Move"
                    }
        return(available_commands)

    # ------------------------- Stone action methods --------------------------
    # These methods only read the state of gm, and always return
    # Message("board action", STPos)

    def attack(self, gm, attack_flag_ID, t):
        cur_x, cur_y, cur_a = self.history[t]

        los_pos = STPos(t, cur_x, cur_y)
        los_pos.step(cur_a)

        while(gm.is_valid_position(los_pos.x, los_pos.y)):
            if gm.board_dynamic[t][los_pos.x][los_pos.y].occupied or (not gm.is_square_available(los_pos.x, los_pos.y)):
                return(Message("destruction", los_pos))
            los_pos.step(cur_a)
        return(Message("pass"))


    # ---------------- LEGACY FEATURE: LOCAL TUI COMPATIBILITY ----------------
    # ------------------------ Command parsing methods ------------------------

    def parse_move_cmd(self, gm):

        # This makes gamemaster add new moves based on the player input and the unique properties of the stone
        # it is called in the game_loop functions
        # this is the method you change when inheriting Stone

        # Default controls: tanks

        # This method must return a Message. If a flag is to be added, it is
        # not done here, but by a dedicated commit method of the Gamemaster.
        # The stone just returns a Message("command", {arguments dictionary}).

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

                if input_cmd_list[0] in ['f', 'fwd', 'forward']:
                    if len(input_cmd_list) == 1:
                        new_a = cur_a
                    else:
                        if input_cmd_list[1] in ['clockwise', 'clock', 'cw', 'c']:
                            new_a = functions.azimuth_addition(cur_a, 1)
                        elif input_cmd_list[1] in ['anticlockwise', 'anti', 'acw', 'a']:
                            new_a = functions.azimuth_addition(cur_a, 3)
                        else:
                            raise Exception("Your input couldn't be parsed")
                    new_x, new_y = functions.pos_step((cur_x, cur_y), cur_a)
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    return(Message("command", {"type" : "spatial_move", "new_x" : new_x, "new_y" : new_y, "new_a" : new_a}))
                if input_cmd_list[0] in ['b', 'bwd', 'backward']:
                    if len(input_cmd_list) == 1:
                        new_a = cur_a
                    else:
                        if input_cmd_list[1] in ['clockwise', 'clock', 'cw', 'c']:
                            new_a = functions.azimuth_addition(cur_a, 1)
                        elif input_cmd_list[1] in ['anticlockwise', 'anti', 'acw', 'a']:
                            new_a = functions.azimuth_addition(cur_a, 3)
                        else:
                            new_a = cur_a
                    new_x, new_y = functions.pos_step((cur_x, cur_y), functions.azimuth_addition(cur_a, 2))
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    return(Message("command", {"type" : "spatial_move", "new_x" : new_x, "new_y" : new_y, "new_a" : new_a}))
                if input_cmd_list[0] in ['t', 'turn']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    new_a = functions.encode_azimuth(input_cmd_list[1])
                    if new_a == None:
                        raise Exception("Your input couldn't be parsed")
                    return(Message("command", {"type" : "spatial_move", "new_x" : cur_x, "new_y" : cur_y, "new_a" : new_a}))
                if input_cmd_list[0] in ['a', 'atk', 'attack']:
                    return(Message("command", {"type" : "attack"}))
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

                if input_cmd_list[0] in ['tj', 'timejump']:
                    if len(input_cmd_list) not in [2, 3]:
                        raise Exception("Required argument missing")
                    target_time = int(input_cmd_list[1])
                    adopted_stone_ID = None
                    if len(input_cmd_list) == 3:
                        adopted_stone_ID = int(input_cmd_list[2])
                    check_timejump_validity_msg = self.check_if_timejump_valid(gm, round_number, t, cur_x, cur_y, cur_a, target_time, cur_x, cur_y, cur_a, adopted_stone_ID)
                    if check_timejump_validity_msg.header == False:
                        raise Exception(check_timejump_validity_msg.msg)
                    return(Message("command", {"type" : "timejump", "new_t" : target_time, "new_x" : cur_x, "new_y" : cur_y, "new_a" : cur_a, "adopted_stone_ID" : adopted_stone_ID}))

                    """if len(input_cmd_list) == 2:
                        # Only time specified
                        target_time = int(input_cmd_list[1])
                        if target_time < 0:
                            raise Exception("Lowest target time value is 0")
                        if target_time >= t:
                            raise Exception("Target time must be in the past")
                        return(Message("command", {"type" : "timejump", "new_t" : target_time, "new_x" : cur_x, "new_y" : cur_y, "new_a" : cur_a}))
                    elif len(input_cmd_list) == 3:
                        # Both time and stone_ID specified; an adoption of a TJI is attempted
                        target_time = int(input_cmd_list[1])
                        adopted_stone_ID = int(input_cmd_list[2])

                        new_t = target_time
                        new_x = cur_x
                        new_y = cur_y
                        new_a = cur_a

                        # Is time correct?
                        if target_time < 0:
                            raise Exception("Lowest target time value is 0")
                        if target_time >= t:
                            raise Exception("Target time must be in the past")

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

                        return(Message("command", {"type" : "timejump", "new_t" : target_time, "new_x" : cur_x, "new_y" : cur_y, "new_a" : cur_a, "adopted_stone_ID" : adopted_stone_ID}))

                    else:
                        raise Exception("Required argument missing")"""

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)


