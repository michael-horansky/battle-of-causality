
import utils.functions as functions
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

from stones.class_Stone import Stone

# -----------------------------------------------------------------------------
# -------------------------------- class Tank ---------------------------------
# -----------------------------------------------------------------------------

class Sniper(Stone):
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        super().__init__(stone_ID, progenitor_flag_ID, player_faction, t_dim)

        self.stone_type = "sniper"

        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "turn/t" : ["azimuth", None, "Faces the specified direction (up/right/down/left)."],
                "attack/atk" : [None, None, "Fires, destroying the stone in line of sight."],
                "timejump/tj" : ["time", "stone ID", "Jumps back into the specified time (spatial position unchanged). If stone ID specified, will swap the time-jump-in which generates said stone."]
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

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)

    # ------------------------- Stone action methods --------------------------
    # These methods only read the state of gm, and always return
    # Message("board action", STPos)

    def attack(self, gm, attack_flag_ID, t):
        cur_x, cur_y, cur_a = self.history[t]

        los_pos = STPos(t, cur_x, cur_y)
        los_pos.step(cur_a)

        while(gm.is_valid_position(los_pos.x, los_pos.y)):
            if gm.board_dynamic[t][los_pos.x][los_pos.y].occupied:
                # Sniper can shoot past stones of the same faction
                if gm.stones[gm.board_dynamic[t][los_pos.x][los_pos.y].stones[0]].player_faction != self.player_faction:
                    return(Message("destruction", los_pos))
            los_pos.step(cur_a)
        return(Message("pass"))


