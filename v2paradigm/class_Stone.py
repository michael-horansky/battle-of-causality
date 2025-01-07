
from functions import *

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

        # The following is the help-log for type specific commands. Change this when inheriting Stone
        # type_specific_commands[command name] = [required args, optional args, message]
        # Use '/' as an alias delimiter and ', ' as an argument delimiter
        self.type_specific_commands = {
                "forward/fwd" : [None, "turn", "Moves forward by 1, turning left/right if specified."],
                "backward/bwd" : [None, "turn", "Moves backward by 1, turning left/right if specified."],
                "turn" : ["azimuth", None, "Faces the specified direction (up/right/down/left)."],
                "attack/atk" : [None, None, "Fires, destroying the stone in line of sight."]
            }


    def print_help_message(self):
        print("You are now placing a command flag for your stone. Select one from the following options.")
        print("(The format is \"" + color.GREEN + "command name" + color.END + " [" + color.BLUE + "arguments" + color.END + ", " + color.CYAN + "optional arguments" + color.END + "]\"  Forward slash denotes alias)")
        print("  -'" + color.GREEN + "help" + color.END + "': Display this message again.")
        print("  -'" + color.GREEN + "quit" + color.END + "/" + color.GREEN + "exit" + color.END + "': Quit the game.")
        print("  -'" + color.GREEN + "undo" + color.END + "': Revert back to commanding the previous stone, erasing the previously placed flag.")
        print("  -'" + color.GREEN + "wait" + color.END + "': The stone will wait in its place. This is also selected on an empty submission!")
        for cmd, options in self.type_specific_commands.items():
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
                # Inheritable help display
                if input_cmd_raw in ['h', 'help']:
                    self.print_help_message()
                    continue

                if input_cmd_raw in ['q', 'quit', 'exit']:
                    print("Quitting the game...")
                    return("quit")

                if input_cmd_raw in ['u', 'undo']:
                    print("Reverting to the previous stone...")
                    return("undo")

                if input_cmd_raw in ['', 'w', 'wait']:
                    new_flag_ID = gm.add_spatial_move(self.ID, t, cur_x, cur_y, cur_x, cur_y, cur_a)
                    return(f"flag_added {new_flag_ID}")





                input_cmd_list = input_cmd_raw.split(' ')

                pos0 = self.get_position(t)
                a0 = self.get_azimuth(t)

                added_move_msg = 0

                if input_cmd_list[0] in ['f', 'fwd', 'forward']:
                    if len(input_cmd_list) <= 1:
                        a1 = a0
                    else:
                        a1 = int(input_cmd_list[1])
                    if np.abs(a0 - a1) == 2: #U-turn
                        print("  This stone can't make a U-turn whilst traversing the board.")
                        return(-1)
                    pos1 = pos_step(pos0, a0)
                    added_move_msg = gm.add_spatial_move(t, pos0, pos1, a1, self.player_faction)
                elif input_cmd_list[0] in ['b', 'bwd', 'backward']:
                    if len(input_cmd_list) <= 1:
                        a1 = a0
                    else:
                        a1 = int(input_cmd_list[1])
                    if np.abs(a0 - a1) == 2: #U-turn
                        print("  This stone can't make a U-turn whilst traversing the board.")
                        return(-1)
                    pos1 = pos_step(pos0, azimuth_addition(a0, 2))
                    added_move_msg = gm.add_spatial_move(t, pos0, pos1, a1, self.player_faction)
                elif input_cmd_list[0] in ['t', 'turn']:
                    if len(input_cmd_list) <= 1:
                        a1 = a0
                    else:
                        a1 = int(input_cmd_list[1])
                    pos1 = pos0
                    added_move_msg = gm.add_spatial_move(t, pos0, pos1, a1, self.player_faction)
                elif input_cmd_list[0] in ['a', 'atk', 'attack']:
                    added_move_msg = gm.add_attack(t, self, allow_friendly_fire = True)
                else:
                    raise Exception("Sus")

                return(added_move_msg)

            except:
                print("Your input couldn't be parsed")
