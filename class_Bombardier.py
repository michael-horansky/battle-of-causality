
from functions import *
from class_STPos import STPos
from class_Message import Message

from class_Stone import Stone

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

    def parse_move_cmd(self, gm, t):

        # This makes gamemaster add new moves based on the player input and the unique properties of the stone
        # it is called in the game_loop functions
        # this is the method you change when inheriting Stone

        # Default controls: tanks

        # This method must return a Message

        cur_x, cur_y, cur_a = self.history[t]
        while(True):
            try:
                input_cmd_raw = input("Input the command in the form \"[command name] [argument]\", or type \"help\": ")

                # Generic commands
                generic_msg = self.parse_generic_move_cmd(gm, input_cmd_raw, cur_x, cur_y)
                if generic_msg.header == "continue":
                    continue
                elif generic_msg.header == "exception":
                    raise Exception(generic_msg.msg)
                elif generic_msg.header == "option":
                    return(generic_msg) # The Gamemaster handles options!


                if input_cmd_raw in ['', 'w', 'wait']:
                    new_flag_ID = gm.add_flag_spatial_move(self.ID, t, cur_x, cur_y, cur_x, cur_y, cur_a)
                    return(Message("flags added", [new_flag_ID]))

                # From now on, we need to consider the command arguments

                input_cmd_list = input_cmd_raw.split(' ')

                if input_cmd_list[0] in ['m', 'move']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    new_a = encode_azimuth(input_cmd_list[1])
                    if new_a == None:
                        raise Exception("Your input couldn't be parsed")
                    new_x, new_y = pos_step((cur_x, cur_y), new_a)
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    new_flag_ID = gm.add_flag_spatial_move(self.ID, t, cur_x, cur_y, new_x, new_y, new_a)
                    return(Message("flags added", [new_flag_ID]))
                if input_cmd_list[0] in ['a', 'atk', 'attack']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    target_time = int(input_cmd_list[1])
                    if target_time < 0:
                        raise Exception("Lowest target time value is 0")
                    if target_time >= t:
                        raise Exception("Target time must be in the past")
                    add_bomb_msg = gm.add_bomb_flag(self.ID, t, cur_x, cur_y, target_time, cur_x, cur_y)
                    if add_bomb_msg.header == "flags added":
                        return(add_bomb_msg)
                    elif add_bomb_msg.header == "exception":
                        raise Exception(add_bomb_msg.msg)
                raise Exception("Your input couldn't be parsed")

            except Exception as e:
                print("Try again;", e)

    def parse_final_move_cmd(self, gm, t):

        # Just the same as parse_move_cdm, except this one is called in the final time-slice. Here, the stones
        # can either pass (if their type allows it), which leaves them causally free so that they can jump back
        # in the next rounds, or they can do a time-jump-out (or some other type-specific action which affects
        # the previous time-slices, not the future ones).
        cur_x, cur_y, cur_a = self.history[t]
        while(True):
            try:
                input_cmd_raw = input("Input the command in the form \"[command name] [argument]\", or type \"help\": ")

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
                        tj_msg = gm.add_flag_timejump(self.ID, t, cur_x, cur_y, self.stone_type, target_time, cur_x, cur_y, cur_a)
                        if tj_msg.header == "flags added":
                            return(tj_msg)
                        elif tj_msg.header == "exception":
                            raise Exception(tj_msg.msg)
                    elif len(input_cmd_list) == 3:
                        # Both time and stone_ID specified; an adoption of a TJI is attempted
                        target_time = int(input_cmd_list[1])
                        adopted_stone_ID = int(input_cmd_list[2])
                        if target_time < 0:
                            raise Exception("Lowest target time value is 0")
                        if target_time >= t:
                            raise Exception("Target time must be in the past")
                        if adopted_stone_ID not in gm.stones:
                            raise Exception("Stone ID invalid")
                        tj_msg = gm.add_flag_timejump(self.ID, t, cur_x, cur_y, gm.stones[adopted_stone_ID].stone_type, target_time, cur_x, cur_y, cur_a, adopted_stone_ID = adopted_stone_ID)
                        if tj_msg.header == "flags added":
                            return(tj_msg)
                        elif tj_msg.header == "exception":
                            raise Exception(tj_msg.msg)
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


