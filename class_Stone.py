
from functions import *
from class_STPos import STPos
from class_Message import Message

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
        self.type_specific_commands = {}
        self.type_specific_final_commands = {}

        self.opposable = True
        self.orientable = False

    def __str__(self):
        return("Stone " + color.DARKCYAN + self.stone_type.upper() + color.END + " (ID " + color.CYAN + str(self.ID) + color.END + ")")

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
        print("(The format is \"" + color.GREEN + "command name" + color.END + " [" + color.BLUE + "arguments" + color.END + "; " + color.CYAN + "optional arguments" + color.END + "]\". Forward slash denotes alias.)")
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

    def attack(self, gm, t, attack_args):
        pass


