
from functions import *

# -------------- Custom exceptions ------------
# We will use these during command parsing, to
# accurately inform the user about what they
# did wrong

"""class UnparsableException(Exception):
    def __init__(self, message='Input not parsable'):
        # Call the base class constructor with the parameters it needs
        super(UnparsableException, self).__init__(message)

class UnparsableException(Exception):
    def __init__(self, message='Input not parsable'):
        # Call the base class constructor with the parameters it needs
        super(UnparsableException, self).__init__(message)"""



# ---------------------------------------------
# ---------------- class Stone ----------------
# ---------------------------------------------

class Stone():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, player_faction, t_dim):

        self.ID = stone_ID
        self.player_faction = player_faction


        self.events = {'death':[], 'time_jump':[]} #keeps track of whether the stone is causally free
        self.causal_freedom_time = 0 # if it spawns into t, it can be moved from t

        self.history = [None] * t_dim # This allows the stone to remember its positions in time, shortening tracking time. [t] = (x,y,a)

        # Generic help-log
        self.generic_commands = {
                "help" : [None, None, "Display the help-log."],
                "quit/exit" : [None, None, "Quit the game."],
                "undo" : [None, None, "Revert back to commanding the previous stone, erasing the previously placed flag."],
                "list_stones/ls": [None, None, "List stones belonging to each player."],
                "list_portals/lp" : ["t, x, y", None, "Lists time-jumps-in on the specified square."],
                "track" : ["ID", None, "Tracks the stone with the specified ID."]
            }

        # The following is the help-log for type specific commands. Change this when inheriting Stone
        # type_specific_commands[command name] = [required args, optional args, message]
        # Use '/' as an alias delimiter and ', ' as an argument delimiter
        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "forward/fwd" : [None, "turn", "Moves forward by 1, turning clockwise/cw or anticlockwise/acw by 90 deg. if specified."],
                "backward/bwd" : [None, "turn", "Moves backward by 1, turning clockwise/cw or anticlockwise/acw by 90 deg. if specified."],
                "turn" : ["azimuth", None, "Faces the specified direction (up/right/down/left)."],
                "attack/atk" : [None, None, "Fires, destroying the stone in line of sight."]
            }

        self.type_specific_final_commands = {
                "pass" : [None, None, "No plag is placed, and this stone remains causally free. This is also selected on an empty submission!"],
                "timejump/tj" : ["time", None, "Jumps back into the specified time (spatial position unchanged)."]
            }

        self.opposable = True

    def display_commands_in_helplog(self, commands):
        for cmd, options in commands.items():
            log_str = "  -'"
            cmd_aliases = cmd.split("/")
            cmd_readable = color.GREEN + (color.END + "/" + color.GREEN).join(cmd_aliases) + color.END
            log_str += cmd_readable
            arg_str = ""
            if not (options[0] == None and options[1] == None):
                arg_str = " ["
                if options[0] != None:
                    req_arg_list = options[0].split(", ")
                    req_args_readable = color.BLUE + (color.END + ", " + color.BLUE).join(req_arg_list) + color.END
                    arg_str += req_args_readable
                if options[1] != None:
                    if options[0] != None:
                        arg_str += '; '
                    opt_arg_list = options[1].split(", ")
                    opt_args_readable = color.CYAN + (color.END + ", " + color.CYAN).join(opt_arg_list) + color.END
                    arg_str += opt_args_readable
                arg_str += "]"
            log_str += arg_str + ": " + options[2]
            print(log_str)

    def print_help_message(self, is_final_command = False):
        print("You are now placing a command flag for your stone. Select one from the following options.")
        print("(The format is \"" + color.GREEN + "command name" + color.END + " [" + color.BLUE + "arguments" + color.END + ", " + color.CYAN + "optional arguments" + color.END + "]\". Forward slash denotes alias.)")
        #print("  -'" + color.GREEN + "help" + color.END + "': Display this message again.")
        #print("  -'" + color.GREEN + "quit" + color.END + "/" + color.GREEN + "exit" + color.END + "': Quit the game.")
        #print("  -'" + color.GREEN + "undo" + color.END + "': Revert back to commanding the previous stone, erasing the previously placed flag.")
        self.display_commands_in_helplog(self.generic_commands)
        if is_final_command:
            available_commands = self.type_specific_final_commands
        else:
            available_commands = self.type_specific_commands
        self.display_commands_in_helplog(available_commands)



    def parse_move_cmd(self, gm, t):

        # This makes gamemaster add new moves based on the player input and the unique properties of the stone
        # it is called in the game_loop functions
        # this is the method you change when inheriting Stone

        # Default controls: tanks

        # If a Flag is added, this method MUST return the message "flag_added [flag_ID]"

        cur_x, cur_y, cur_a = self.history[t]
        while(True):
            try:
                input_cmd_raw = input("Input the command in the form \"[command name] [argument]\", or type \"help\": ")
                # Generic commands
                if input_cmd_raw in ['h', 'help']:
                    self.print_help_message(False)
                    continue

                if input_cmd_raw in ['q', 'quit', 'exit']:
                    print("Quitting the game...")
                    return("quit")

                if input_cmd_raw in ['u', 'undo']:
                    print("Reverting to the previous stone...")
                    return("undo")

                if input_cmd_raw in ['list_stones', 'ls']:
                    gm.print_stone_list()
                    continue



                if input_cmd_raw in ['', 'w', 'wait']:
                    new_flag_ID = gm.add_flag_spatial_move(self.ID, t, cur_x, cur_y, cur_x, cur_y, cur_a)
                    return(f"flag_added {new_flag_ID}")

                # From now on, we need to consider the command arguments

                input_cmd_list = input_cmd_raw.split(' ')

                if input_cmd_list[0] in ['f', 'fwd', 'forward']:
                    if len(input_cmd_list) == 1:
                        new_a = cur_a
                    else:
                        if input_cmd_list[1] in ['clockwise', 'clock', 'cw', 'c']:
                            new_a = azimuth_addition(cur_a, 1)
                        elif input_cmd_list[1] in ['anticlockwise', 'anti', 'acw', 'a']:
                            new_a = azimuth_addition(cur_a, 3)
                        else:
                            raise Exception("Your input couldn't be parsed")
                    new_x, new_y = pos_step((cur_x, cur_y), cur_a)
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    new_flag_ID = gm.add_flag_spatial_move(self.ID, t, cur_x, cur_y, new_x, new_y, new_a)
                    return(f"flag_added {new_flag_ID}")
                if input_cmd_list[0] in ['b', 'bwd', 'backward']:
                    if len(input_cmd_list) == 1:
                        new_a = cur_a
                    else:
                        if input_cmd_list[1] in ['clockwise', 'clock', 'cw', 'c']:
                            new_a = azimuth_addition(cur_a, 1)
                        elif input_cmd_list[1] in ['anticlockwise', 'anti', 'acw', 'a']:
                            new_a = azimuth_addition(cur_a, 3)
                        else:
                            new_a = cur_a
                    new_x, new_y = pos_step((cur_x, cur_y), azimuth_addition(cur_a, 2))
                    if not gm.is_square_available(new_x, new_y):
                        # The stone is attempting to move into a wall
                        raise Exception("Invalid move")
                    new_flag_ID = gm.add_flag_spatial_move(self.ID, t, cur_x, cur_y, new_x, new_y, new_a)
                    return(f"flag_added {new_flag_ID}")
                if input_cmd_list[0] in ['t', 'turn']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    new_a = encode_azimuth(input_cmd_list[1])
                    if new_a == None:
                        raise Exception("Your input couldn't be parsed")
                    new_flag_ID = gm.add_flag_spatial_move(self.ID, t, cur_x, cur_y, cur_x, cur_y, new_a)
                    return(f"flag_added {new_flag_ID}")
                if input_cmd_list[0] in ['a', 'atk', 'attack']:
                    new_flag_ID = gm.add_flag_attack(self.ID, t, cur_x, cur_y, allow_friendly_fire = True)
                    return(f"flag_added {new_flag_ID}")
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
                # Inheritable help display
                if input_cmd_raw in ['h', 'help']:
                    self.print_help_message(True)
                    continue

                if input_cmd_raw in ['q', 'quit', 'exit']:
                    print("Quitting the game...")
                    return("quit")

                if input_cmd_raw in ['u', 'undo']:
                    print("Reverting to the previous stone...")
                    return("undo")

                if input_cmd_raw in ['', 'p', 'pass']:
                    return("pass")

                # From now on, we need to consider the command arguments

                input_cmd_list = input_cmd_raw.split(' ')

                if input_cmd_list[0] in ['tj', 'timejump']:
                    if len(input_cmd_list) == 1:
                        raise Exception("Required argument missing")
                    # TODO give an option of "adopting" an inactive (or maybe even an active?) TJI
                    target_time = int(input_cmd_list[1])
                    if target_time < 0:
                        raise Exception("Lowest target time value is 0")
                    if target_time >= t:
                        raise Exception("Target time must be in the past")
                    tjo_ID, tji_ID = gm.add_flag_timejump(self.ID, t, cur_x, cur_y, target_time, cur_x, cur_y, cur_a)
                    return(f"flag_added {tjo_ID} {tji_ID}")

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)
