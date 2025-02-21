
import utils.functions as functions
import utils.constants as constants
from game_logic.class_STPos import STPos
from game_logic.class_Message import Message

# -----------------------------------------------------------------------------
# -------------------------------- class Stone --------------------------------
# -----------------------------------------------------------------------------

class Stone():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, stone_ID, progenitor_flag_ID, player_faction, t_dim):

        self.stone_type = "undefined"

        self.ID = stone_ID
        self.progenitor_flag_ID = progenitor_flag_ID
        self.player_faction = player_faction

        self.history = [None] * t_dim # This allows the stone to remember its positions in time, shortening tracking time. [t] = (x,y,a)

        # Trackers for tagscreen interactions
        self.has_been_tag_locked = False
        self.has_been_tag_unlocked_this_turn = False
        self.unlock_tag_max_flag_ID_this_turn = None
        self.has_been_tag_hidden_this_turn = False

        # Generic help-log
        self.generic_commands = {
                "help" : [None, None, "Display the help-log."],
                "quit/exit" : [None, None, "Quit the game."],
                "undo" : [None, None, "Revert back to commanding the previous stone, erasing the previously placed flag."],
                "list_stones/ls": [None, None, "List stones belonging to each player."],
                "list_portals/lp" : ["t", "x, y", "Lists time-jumps-in on the specified square. Position defaults to stone position."],
                "track" : ["ID/t, x, y", None, "Tracks the stone with the specified ID. Alternatively, tracks the stone placed at a specific position."],
                "worldline/wl" : ["ID/t, x, y", None, "Shows the worldline to which the stone with the specified ID, or at the specified position, belongs."]
            }

        # The following is the help-log for type specific commands. Change this when inheriting Stone
        # type_specific_commands[command name] = [required args, optional args, message]
        # Use '/' as an alias delimiter and ', ' as an argument delimiter
        self.type_specific_commands = {}
        self.type_specific_final_commands = {}

        self.opposable = True
        self.orientable = False

    def reset_temporary_trackers(self):
        self.has_been_tag_locked = False
        self.has_been_tag_unlocked_this_turn = False
        self.unlock_tag_max_flag_ID_this_turn = None
        self.has_been_tag_hidden_this_turn = False

    def reset_temporary_time_specific_trackers(self):
        self.has_been_tag_unlocked_this_turn = False
        self.unlock_tag_max_flag_ID_this_turn = None
        self.has_been_tag_hidden_this_turn = False

    def __str__(self):
        return("Stone " + constants.color.DARKCYAN + self.stone_type.upper() + constants.color.END + " (ID " + constants.color.CYAN + str(self.ID) + constants.color.END + ")")

    def display_commands_in_helplog(self, commands):
        for cmd, options in commands.items():
            log_str = "  -'"
            cmd_aliases = cmd.split("/")
            cmd_readable = constants.color.GREEN + (constants.color.END + "/" + constants.color.GREEN).join(cmd_aliases) + constants.color.END
            log_str += cmd_readable
            arg_str = ""
            if not (options[0] == None and options[1] == None):
                arg_str = " ["
                if options[0] != None:
                    # First we split the aliases (overloading), then each alias into arguments
                    req_arg_alias_list = options[0].split("/")
                    for i in range(len(req_arg_alias_list)):
                        req_arg_list = req_arg_alias_list[i].split(", ")
                        req_arg_alias_list[i] = constants.color.BLUE + (constants.color.END + ", " + constants.color.BLUE).join(req_arg_list) + constants.color.END
                    arg_str += "/".join(req_arg_alias_list)
                if options[1] != None:
                    if options[0] != None:
                        arg_str += '; '
                    opt_arg_list = options[1].split(", ")
                    opt_args_readable = constants.color.CYAN + (constants.color.END + ", " + constants.color.CYAN).join(opt_arg_list) + constants.color.END
                    arg_str += opt_args_readable
                arg_str += "]"
            log_str += arg_str + ": " + options[2]
            print(log_str)

    def print_help_message(self, is_final_command = False):
        print("You are now placing a command flag for your stone. Select one from the following options.")
        print("(The format is \"" + constants.color.GREEN + "command name" + constants.color.END + " [" + constants.color.BLUE + "arguments" + constants.color.END + "; " + constants.color.CYAN + "optional arguments" + constants.color.END + "]\". Forward slash denotes alias.)")
        self.display_commands_in_helplog(self.generic_commands)
        if is_final_command:
            available_commands = self.type_specific_final_commands
        else:
            available_commands = self.type_specific_commands
        self.display_commands_in_helplog(available_commands)

    def parse_generic_move_cmd(self, gm, cmd_raw, x, y, is_final_command = False):
        # Generic commands
        if cmd_raw in ['h', 'help']:
            self.print_help_message(is_final_command)
            return(Message("continue"))

        if cmd_raw in ['q', 'quit', 'exit']:
            print("Quitting the game...")
            return(Message("option", "quit"))

        if cmd_raw in ['u', 'undo']:
            print("Reverting to the previous stone...")
            return(Message("option", "undo"))

        if cmd_raw in ['list_stones', 'ls']:
            gm.print_stone_list()
            return(Message("continue"))

        cmd_raw_list = cmd_raw.split(" ")
        if cmd_raw_list[0] in ['list_portals', 'lp']:
            if len(cmd_raw_list) == 2:
                try:
                    target_time = int(cmd_raw_list[1])
                    gm.print_time_portals(target_time, x, y)
                    return(Message("continue"))
                except:
                    return(Message("exception", "Submitted argument not formatted like an integer"))
            elif len(cmd_raw_list) == 4:
                try:
                    target_time = int(cmd_raw_list[1])
                    target_x = int(cmd_raw_list[2])
                    target_y = int(cmd_raw_list[3])
                    gm.print_time_portals(target_time, target_x, target_y)
                    return(Message("continue"))
                except:
                    return(Message("exception", "Submitted argument not formatted like integers"))
            else:
                return(Message("exception", "Mismatched number of arguments"))

        if cmd_raw_list[0] in ['track']:
            if len(cmd_raw_list) == 2:
                try:
                    target_ID = int(cmd_raw_list[1])
                    gm.print_stone_tracking(target_ID)
                    return(Message("continue"))
                except:
                    return(Message("exception", "Submitted argument not formatted like an integer"))
            elif len(cmd_raw_list) == 4:
                try:
                    target_time = int(cmd_raw_list[1])
                    target_x = int(cmd_raw_list[2])
                    target_y = int(cmd_raw_list[3])
                    gm.print_stone_tracking(STPos(target_time, target_x, target_y))
                    return(Message("continue"))
                except:
                    return(Message("exception", "Submitted argument not formatted like integers"))
            else:
                return(Message("exception", "Mismatched number of arguments"))

        return(Message("not a generic cmd"))

    def check_if_timejump_valid(self, gm, round_number, old_t, old_x, old_y, old_a, new_t, new_x, new_y, new_a, adopted_stone_ID = None):

        # Returns Message(True) if timejump valid, or Message(False, "message") if invalid
        if self.has_been_tag_locked:
            return(Message(False, "This stone has been tag locked, and thus cannot perform a new time-jump-out."))
        if new_t < 0:
            return(Message(False, "Lowest target time value is 0"))
        if new_t >= gm.t_dim:
            return(Message(False, f"Largest target time value is {gm.t_dim - 1}"))
        if new_t >= old_t:
            return(Message(False, "Target time must be in the past"))
        if not gm.is_square_available(new_x, new_y):
            # The stone is attempting to move into a wall
            return(Message(False, "Target spatial position not available"))
        if adopted_stone_ID is not None:
            if adopted_stone_ID not in gm.stones:
                return(Message(False, "Adopted stone ID invalid"))
            adopted_stone_progenitor = gm.stones[adopted_stone_ID].progenitor_flag_ID
            if gm.flags[adopted_stone_progenitor].flag_type != "time_jump_in":
                return(Message(False, "Specified stone is not placed onto the board via a time-jump-in"))
            if not (gm.flags[adopted_stone_progenitor].pos.t == new_t - 1 and gm.flags[adopted_stone_progenitor].pos.x == new_x and gm.flags[adopted_stone_progenitor].pos.y == new_y):
                return(Message(False, "Specified stone doesn't time-jump-in at the specified square"))
            if self.player_faction != gm.stones[adopted_stone_ID].player_faction:
                return(Message(False, "Specified stone belongs to a different faction"))
            if self.stone_type not in [gm.stones[adopted_stone_ID].stone_type, "wildcard"]:
                return(Message(False, "Specified stone is of incompatible type"))
            if self.orientable and gm.flags[adopted_stone_progenitor].flag_args[1] != new_a:
                # If this is a wildcard, then the adopted stone can be orientable with any azimuth
                return(Message(False, "Specified stone jumps in at a different azimuth than proposed"))

            for TJI_ID in gm.effects_by_round[round_number]:
                if TJI_ID == adopted_stone_progenitor:
                    return(Message(False, "Specified time-jump-in has been added only this round, and thus hasn't been realised yet."))
        return(Message(True))

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

                raise Exception("Your input couldn't be parsed")

            except ValueError:
                print("Try again; Arguments with numerical inputs should be well-formatted")
            except Exception as e:
                print("Try again;", e)

    # ------------------------- Stone action methods --------------------------
    # These methods only read the state of gm, and always return
    # Message("board action", STPos)

    def attack(self, gm, attack_flag_ID, t):
        return(Message("pass"))


