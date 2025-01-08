
from functions import *
from class_STPos import STPos

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
                "list_portals/lp" : ["t", "x, y", "Lists time-jumps-in on the specified square. Position defaults to stone position."],
                "track" : ["ID/t, x, y", None, "Tracks the stone with the specified ID. Alternatively, tracks the stone placed at a specific position."]
            }

        # The following is the help-log for type specific commands. Change this when inheriting Stone
        # type_specific_commands[command name] = [required args, optional args, message]
        # Use '/' as an alias delimiter and ', ' as an argument delimiter
        self.stone_type = "tank"
        self.type_specific_commands = {
                "wait" : [None, None, "The stone will wait in its place. This is also selected on an empty submission!"],
                "forward/fwd" : [None, "turn", "Moves forward by 1, turning clockwise/cw or anticlockwise/acw by 90 deg. if specified."],
                "backward/bwd" : [None, "turn", "Moves backward by 1, turning clockwise/cw or anticlockwise/acw by 90 deg. if specified."],
                "turn" : ["azimuth", None, "Faces the specified direction (up/right/down/left)."],
                "attack/atk" : [None, None, "Fires, destroying the stone in line of sight."]
            }

        self.type_specific_final_commands = {
                "pass" : [None, None, "No plag is placed, and this stone remains causally free. This is also selected on an empty submission!"],
                "timejump/tj" : ["time", "stone ID", "Jumps back into the specified time (spatial position unchanged). If stone ID specified, will adopt a time-jump-in which generates said stone."]
            }

        self.opposable = True

    def __str__(self):
        return("Stone " + color.DARKCYAN + "TANK" + color.END + " (ID " + color.CYAN + str(self.ID) + color.END + ")")

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
                    # First we split the aliases (overloading), then each alias into arguments
                    req_arg_alias_list = options[0].split("/")
                    for i in range(len(req_arg_alias_list)):
                        req_arg_list = req_arg_alias_list[i].split(", ")
                        req_arg_alias_list[i] = color.BLUE + (color.END + ", " + color.BLUE).join(req_arg_list) + color.END
                    arg_str += "/".join(req_arg_alias_list)
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

    def parse_generic_move_cmd(self, gm, cmd_raw, x, y):
        # Generic commands
        if cmd_raw in ['h', 'help']:
            self.print_help_message(False)
            return("success")

        if cmd_raw in ['q', 'quit', 'exit']:
            print("Quitting the game...")
            return("quit")

        if cmd_raw in ['u', 'undo']:
            print("Reverting to the previous stone...")
            return("undo")

        if cmd_raw in ['list_stones', 'ls']:
            gm.print_stone_list()
            return("success")

        cmd_raw_list = cmd_raw.split(" ")
        if cmd_raw_list[0] in ['list_portals', 'lp']:
            if len(cmd_raw_list) == 2:
                try:
                    target_time = int(cmd_raw_list[1])
                    gm.print_time_portals(target_time, x, y)
                    return("success")
                except:
                    return("except Submitted argument not formatted like an integer")
            elif len(cmd_raw_list) == 4:
                try:
                    target_time = int(cmd_raw_list[1])
                    target_x = int(cmd_raw_list[2])
                    target_y = int(cmd_raw_list[3])
                    gm.print_time_portals(target_time, target_x, target_y)
                    return("success")
                except:
                    return("except Submitted arguments not formatted like an integer")
            else:
                return("except Mismatched number of arguments")

        if cmd_raw_list[0] in ['track']:
            if len(cmd_raw_list) == 2:
                try:
                    target_ID = int(cmd_raw_list[1])
                    gm.print_stone_tracking(target_ID)
                    return("success")
                except:
                    return("except Submitted argument not formatted like an integer")
            elif len(cmd_raw_list) == 4:
                try:
                    target_time = int(cmd_raw_list[1])
                    target_x = int(cmd_raw_list[2])
                    target_y = int(cmd_raw_list[3])
                    gm.print_stone_tracking(STPos(target_time, target_x, target_y))
                    return("success")
                except:
                    return("except Submitted arguments not formatted like an integer")
            else:
                return("except Mismatched number of arguments")

        return("fail")



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
                generic_msg = self.parse_generic_move_cmd(gm, input_cmd_raw, cur_x, cur_y)
                generic_msg_list = generic_msg.split(' ')
                if generic_msg_list[0] == "success":
                    continue
                elif generic_msg_list[0] == "except":
                    raise Exception(" ".join(generic_msg_list[1:]))
                elif generic_msg_list[0] != "fail":
                    return(generic_msg)


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

                # Generic commands
                generic_msg = self.parse_generic_move_cmd(gm, input_cmd_raw, cur_x, cur_y)
                generic_msg_list = generic_msg.split(' ')
                if generic_msg_list[0] == "success":
                    continue
                elif generic_msg_list[0] == "except":
                    raise Exception(" ".join(generic_msg_list[1:]))
                elif generic_msg_list[0] != "fail":
                    return(generic_msg)


                if input_cmd_raw in ['', 'p', 'pass']:
                    return("pass")

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
                        tjo_ID, tji_ID = gm.add_flag_timejump(self.ID, t, cur_x, cur_y, target_time, cur_x, cur_y, cur_a)
                        return(f"flag_added {tjo_ID} {tji_ID}")
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
                        created_flags = gm.add_flag_timejump(self.ID, t, cur_x, cur_y, target_time, cur_x, cur_y, cur_a, adopted_stone_ID = adopted_stone_ID)
                        if isinstance(created_flags, str):
                            # We got a log instead
                            cmd_msg_list = created_flags.split(" ")
                            if cmd_msg_list[0] == "except":
                                raise Exception(" ".join(cmd_msg_list[1:]))
                            raise Exception("Unknown log received")
                        return(f"flag_added {" ".join(str(item_ID) for item_ID in created_flags)}")
                    else:
                        raise Exception("Required argument missing")

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)
