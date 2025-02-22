
import utils.functions as functions
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

from stones.class_Stone import Stone

# -----------------------------------------------------------------------------
# ----------------------------- class Bombardier ------------------------------
# -----------------------------------------------------------------------------

class Wildcard(Stone):
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        super().__init__(stone_ID, progenitor_flag_ID, player_faction, t_dim)

        self.stone_type = "wildcard"

        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "move/m" : ["direction", None, "Moves in specified diagonal direction by 1 square (upright, downright, downleft, upleft). Destroys other stones on the final square as if capturing in chess."],
                "timejump/tj" : ["time", "stone ID", "Jumps back into the specified time (spatial position unchanged). If stone ID specified, will swap the time-jump-in which generates said stone (can be of any type)."]
            }

        self.type_specific_final_commands = {
                "pass" : [None, None, "No plag is placed, and this stone remains causally free. This is also selected on an empty submission!"],
                "timejump/tj" : ["time", "stone ID", "Jumps back into the specified time (spatial position unchanged). If stone ID specified, will swap the time-jump-in which generates said stone (can be of any type)."]
            }

        self.opposable = False
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
                    return(Message("command", {"type" : "spatial_move", "new_x" : cur_x, "new_y" : cur_y, "new_a" : 0}))

                # From now on, we need to consider the command arguments

                input_cmd_list = input_cmd_raw.split(' ')

                if input_cmd_list[0] in ['m', 'move']:
                    if len(input_cmd_list) not in [2]:
                        raise Exception("Required argument missing")
                    d_pos = functions.diag_direction_to_delta_pos(input_cmd_list[1])
                    if d_pos is None:
                        raise Exception("Your input couldn't be parsed")
                    d_x, d_y = d_pos
                    new_x = cur_x + d_x
                    new_y = cur_y + d_y
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    return(Message("command", {"type" : "spatial_move", "new_x" : new_x, "new_y" : new_y, "new_a" : 1}))
                # NOTE: We 'cheat' when marking the Wildcard as explosive on movement, because we tell apart waiting from moving
                # by checking the new azimuth, which is always 0 for waiting and 1 for moving (azimuth doesn't manifest for unorientable stones)

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
        # This stone doesn't have an attack action; instead, the 'attack' cmd
        # places a bomb effect flag, as resolved in self.parse_move_cdm()
        # The attack flag is placed as a cause tracker.
        return(Message("pass"))


