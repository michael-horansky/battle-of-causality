
import utils.functions as functions
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

from stones.class_Stone import Stone

# -----------------------------------------------------------------------------
# ----------------------------- class Bombardier ------------------------------
# -----------------------------------------------------------------------------

class Bombardier(Stone):
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        super().__init__(stone_ID, progenitor_flag_ID, player_faction, t_dim)

        self.stone_type = "bombardier"

        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "move/m" : ["direction", None, "Moves in specified direction by 1 square."],
                "attack/atk" : ["time", None, "Drops a bomb back in time onto the same spatial position. Target time has to be in the past!"]
            }

        self.type_specific_final_commands = {
                "pass" : [None, None, "No plag is placed, and this stone remains causally free. This is also selected on an empty submission!"],
                "timejump/tj" : ["time", "stone ID", "Jumps back into the specified time (spatial position unchanged). If stone ID specified, will adopt a time-jump-in which generates said stone."]
            }

        self.opposable = True
        self.orientable = False

    # -------------------------------------------------------------------------
    # -------------------------- Overridden methods ---------------------------
    # -------------------------------------------------------------------------

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

                if input_cmd_list[0] in ['m', 'move']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    new_a = functions.encode_azimuth(input_cmd_list[1])
                    if new_a == None:
                        raise Exception("Your input couldn't be parsed")
                    new_x, new_y = functions.pos_step((cur_x, cur_y), new_a)
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    return(Message("command", {"type" : "spatial_move", "new_x" : new_x, "new_y" : new_y, "new_a" : new_a}))
                if input_cmd_list[0] in ['a', 'atk', 'attack']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    target_time = int(input_cmd_list[1])
                    if target_time < 0:
                        raise Exception("Lowest target time value is 0")
                    if target_time >= t:
                        raise Exception("Target time must be in the past")

                    return(Message("command", {"type" : "attack", "target_t" : target_time}))
                raise Exception("Your input couldn't be parsed")

            except Exception as e:
                print("Try again;", e)

    def parse_final_move_cmd(self, gm):

        # Just the same as parse_move_cdm, except this one is called in the final time-slice. Here, the stones
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
                    if len(input_cmd_list) == 2:
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
                        raise Exception("Required argument missing")

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)

    # ------------------------- Stone action methods --------------------------
    # These methods only read the state of gm, and always return
    # Message("board action", STPos)

    def attack(self, gm, t, attack_args):
        # This stone doesn't have an attack action; instead, the 'attack' cmd
        # places a bomb effect flag, as resolved in self.parse_move_cdm()
        # The attack flag is placed as a cause tracker.
        return(Message("pass"))


