

import math
from functions import *
from class_STPos import STPos
from class_Message import Message
from class_Stone import Stone
from class_Flag import Flag
from class_Board_square import Board_square

# ---------------------------------------------
# ------------- class Gamemaster --------------
# ---------------------------------------------

class Gamemaster():

    # ----------------------------------------------------
    # ------ constructors, destructors, descriptors ------
    # ----------------------------------------------------

    def __init__(self, board_number, display_logs = False):

        self.display_logs = display_logs

        self.print_log("Initialising game trackers and memory bins...",)

        # Stone trackers. The lists are updated when flags are placed, and do not depend on which stones are actually present on the board dynamically.
        self.stones = {} #[ID] = Stone()
        self.faction_armies = {} #[faction] = [ID_1, ID_2 ... ]
        self.factions = ['A', 'B']
        # Setup trackers
        self.setup_stones = {} # Tracker for stones which are added on board setup. This is used when resolving paradoxes. [stone_ID] = flag_ID
        self.removed_setup_stones = {} # [stone_ID] = flag_ID

        # the board
        self.board_static = [] # [x][y] = type
        self.board_dynamic = [] # [t][x][y] = Board_square
        self.conflicting_squares = [] # [t] = (x,y) of a board square which is occupied by more than one stone at time t
        self.setup_squares = [] # this acts as board_dynamic with t = -1, and only accepts stone creating flags

        # flags
        self.flags = {} # [flag_ID] = Flag()

        # Trackers for existing time-jumps
        self.tji_ID_list = [] # This list is always ordered in an ascending order
        self.tji_bearing = {} # This updates on every self.execute_moves. [tji_ID] = number of activated matching TJOs
        self.timejump_bijection = {} # This is the recorded bijection of active TJIs. [tji_ID] = tjo_ID, where tjo_ID marks the TJO which actually activates
        self.stone_inheritance = {} # [stone_ID] = child_ID

        # Trackers for newly added time-jumps
        self.tji_ID_buffer = {} # TJIs added before the next scenario selection (after each selection, they flush into tji_ID_list). [new tji_ID] = new tjo_ID

        # TUI elements
        self.board_delim = ' | '

        self.load_board(board_number)

    def add_stone_on_setup(self, faction, x, y, a0):
        # This function allows Gamemaster to describe the initial state of the board, which is reverted to for every retrace of causal events
        new_flag = Flag(STPos(-1, x, y), 'add_stone', faction, [True, a0])
        self.setup_squares[x][y].add_flag(new_flag.flag_ID, new_flag.stone_ID)
        self.flags[new_flag.flag_ID] = new_flag

        # Trackers
        self.stones[new_flag.stone_ID] = Stone(new_flag.stone_ID, faction, self.t_dim)
        self.faction_armies[faction].append(new_flag.stone_ID)
        self.setup_stones[new_flag.stone_ID] = new_flag.flag_ID

    def load_board(self, board_number):
        # load spatial and temporal dimensions of the board from the provided txt file
        self.print_log(f"Loading board {board_number}...", 0)

        self.print_log("Reading board source file...", 1)
        board_file = open("resources/boards/board_" + uniform_str(board_number, 3) + ".txt", 'r')
        board_lines = board_file.readlines()
        board_file.close()

        for i in range(len(board_lines)):
            if board_lines[i][-1] == '\n':
                board_lines[i] = board_lines[i][:-1]

        self.x_dim = len(board_lines[1])
        self.y_dim = len(board_lines) - 1

        # initialize the board matrix, indexed as M[x][y]

        self.board_static = []
        for i in range(self.x_dim):
            self.board_static.append([' ']*self.y_dim)

        # Initialize the board initializing flags
        self.flags = {}
        self.setup_squares = []
        for x in range(self.x_dim):
            self.setup_squares.append([])
            for y in range(self.y_dim):
                self.setup_squares[x].append(Board_square(STPos(-1, x, y)))

        self.t_dim = int(board_lines[0])

        # Setup players
        self.stones = {}
        self.faction_armies = {}
        self.setup_stones = {}
        self.removed_setup_stones = {}
        for faction in self.factions:
            self.faction_armies[faction] = []

        faction_orientations = {'A': 1, 'B' : 3} #TODO load this from the board dynamically

        # Read the board setup
        for y in range(self.y_dim):
            for x in range(self.x_dim):
                cur_char = board_lines[y+1][x]
                if cur_char.upper() in self.factions:
                    self.add_stone_on_setup(cur_char.upper(), x, y, faction_orientations[cur_char.upper()])
                else:
                    self.board_static[x][y] = cur_char

        # Setup dynamic board squares
        self.print_log("Setting up dynamic board representation...", 1)
        self.board_dynamic = []
        for t in range(self.t_dim):
            self.board_dynamic.append([])
            for x in range(self.x_dim):
                self.board_dynamic[t].append([])
                for y in range(self.y_dim):
                    self.board_dynamic[t][x].append(Board_square(STPos(t, x, y)))

        self.conflicting_squares = repeated_list(self.t_dim, [])

        # Calculate TUI parameters for printing
        self.single_board_width = self.x_dim * 2 + len(str(self.y_dim - 1))
        self.header_width = self.single_board_width * self.t_dim + len(self.board_delim) * (self.t_dim - 1)

    # ----------------- Print functions -------------------------

    def print_heading_message(self, msg, level):
        # smaller the level, bigger the header
        header_size = self.header_width#(self.x_dim * 2 - 1) * self.t_dim + 3 * (self.t_dim - 1)
        if level == 0:
            print(color.BOLD + '-' * header_size + color.LIGHT)
            print(color.BOLD + st(' ' + msg + ' ', header_size, '-') + color.LIGHT)
            print(color.BOLD + '-' * header_size + color.LIGHT)
        if level == 1:
            print(color.BOLD + st(' ' + msg + ' ', header_size, '-') + color.LIGHT)
        if level == 2:
            print('-' * int(header_size / 4) + ' ' + color.BOLD + msg + color.LIGHT)
        if level >= 3:
            print("# " + color.BOLD + msg + color.LIGHT)

    def print_log(self, msg, lvl = 0):
        if self.display_logs:
            print(" " * lvl * 4 + "[" + msg + "]")

    def print_board_at_time(self, t, print_to_output = True, include_header_line = False, is_active = False, track_stone_ID = -1):

        def print_stone(board_lines, stone_symbol, stone_position, stone_azimuth, is_causally_free = False, is_tracked = False):
            if stone_position == -1 or stone_azimuth == -1:
                return(-1)
            stone_x, stone_y = stone_position
            stone_a = stone_azimuth
            cur_x = stone_x * 2
            cur_y = stone_y * 2

            stone_formatting_pre = ''
            stone_formatting_suf = ''
            if is_causally_free:
                stone_formatting_pre += color.BOLD
                stone_formatting_suf += color.LIGHT
            if is_tracked:
                stone_formatting_pre += color.CYAN
                if is_active:
                    stone_formatting_suf += color.GREEN
                else:
                    stone_formatting_suf += color.END

            board_lines[cur_y][cur_x] = stone_formatting_pre + stone_symbol + stone_formatting_suf
            if stone_a == 0:
                cur_y -= 1
                if board_lines[cur_y][cur_x] == 'v':
                    board_lines[cur_y][cur_x] = 'X'
                else:
                    board_lines[cur_y][cur_x] = '^'
            if stone_a == 1:
                cur_x += 1
                if board_lines[cur_y][cur_x] == '<':
                    board_lines[cur_y][cur_x] = 'X'
                else:
                    board_lines[cur_y][cur_x] = '>'
            if stone_a == 2:
                cur_y += 1
                if board_lines[cur_y][cur_x] == '^':
                    board_lines[cur_y][cur_x] = 'X'
                else:
                    board_lines[cur_y][cur_x] = 'v'
            if stone_a == 3:
                cur_x -= 1
                if board_lines[cur_y][cur_x] == '>':
                    board_lines[cur_y][cur_x] = 'X'
                else:
                    board_lines[cur_y][cur_x] = '<'

        # board lines: list of rows
        board_lines = repeated_list(self.y_dim * 2 - 1, repeated_list(self.x_dim * 2 - 1, ' '))
        for y in range(self.y_dim):
            for x in range(self.x_dim):
                # Static board properties
                board_lines[2 * y][2 * x] = self.board_static[x][y]
                # Dynamic board properties

                # Stones
                if self.board_dynamic[t][x][y].occupied:
                    occupant_ID = self.board_dynamic[t][x][y].stones[0]
                    is_occupant_causally_free = occupant_ID in self.board_dynamic[t][x][y].causally_free_stones
                    print_stone(board_lines, self.stones[occupant_ID].player_faction, (x, y), self.board_dynamic[t][x][y].stone_properties[occupant_ID][0], is_causally_free = is_occupant_causally_free, is_tracked = (track_stone_ID == occupant_ID))

                # Timejumps
                # An active TJI is bg.ORANGE, an active TJO is bg.PURPLE. Inactive portals of either kind are bg.BLACK. Conflicts are bg.RED
                has_active_TJI = False
                has_inactive_TJI = False
                has_active_TJO = False
                has_inactive_TJO = False
                has_conflict = False
                TJI_square = None
                if t > 0:
                    TJI_square = self.board_dynamic[t-1][x][y]
                else:
                    TJI_square = self.setup_squares[x][y]
                for cur_flag_ID in TJI_square.flags:
                    if has_conflict:
                        break
                    if self.flags[cur_flag_ID].flag_type == "time_jump_in":
                        if cur_flag_ID in self.timejump_bijection.keys():
                            # Active TJI
                            if has_active_TJI or has_active_TJO:
                                # Conflict!
                                has_conflict = True
                            has_active_TJI = True
                        else:
                            # Inactive TJI
                            has_inactive_TJI = True
                for cur_flag_ID in self.board_dynamic[t][x][y].flags:
                    if has_conflict:
                        break
                    if self.flags[cur_flag_ID].flag_type == "time_jump_out":
                        if cur_flag_ID in self.timejump_bijection.values():
                            # Active TJI
                            if has_active_TJI or has_active_TJO:
                                # Conflict!
                                has_conflict = True
                            has_active_TJO = True
                        else:
                            # Inactive TJI
                            has_inactive_TJO = True
                if has_conflict:
                    board_lines[2 * y][2 * x] = color.bg.RED + board_lines[2 * y][2 * x] + color.bg.DEFAULT
                elif has_active_TJI:
                    board_lines[2 * y][2 * x] = color.bg.ORANGE + board_lines[2 * y][2 * x] + color.bg.DEFAULT
                elif has_active_TJO:
                    board_lines[2 * y][2 * x] = color.bg.PURPLE + board_lines[2 * y][2 * x] + color.bg.DEFAULT
                elif has_inactive_TJO or has_inactive_TJI:
                    board_lines[2 * y][2 * x] = color.bg.BLACK + board_lines[2 * y][2 * x] + color.bg.DEFAULT

        for i in range(len(board_lines)):
            board_lines[i] = ''.join(board_lines[i])

        # if active, we highlight the board in green

        if is_active:
            for i in range(len(board_lines)):
                board_lines[i] = color.GREEN + board_lines[i] + color.END

        # If header line included, we inscribe t on top and x,y labels on the left and bottom.

        if include_header_line:
            # First, the y labels
            max_y_width = len(str(self.y_dim - 1))
            for i in range(len(board_lines)):
                board_lines[i] = " " * (max_y_width + 1) + board_lines[i]
            for y in range(self.y_dim):
                board_lines[2 * y] = color.RED + uniform_str(str(y), max_y_width, ' ') + color.END + board_lines[2 * y][max_y_width:]

            # Then, the x labels
            max_x_width = len(str(self.x_dim - 1))
            if max_x_width == 1:
                #board_lines.append(" " * self.single_board_width)
                x_label_string = " " * (max_y_width + 1)
                for x in range(self.x_dim):
                    x_label_string += str(x) + " "
                board_lines.append(color.RED + x_label_string[:-1] + color.END)
            if max_x_width == 2:
                x_label_str = [" " * (max_y_width)]*2
                for x in range(self.x_dim):
                    x_label_str[ x      % 2] += " " * 2
                    x_label_str[(x + 1) % 2] += uniform_str(str(x), 2, " ")
                board_lines.append(color.RED + x_label_str[0] + color.END)
                board_lines.append(color.RED + x_label_str[1] + color.END)



            header_info = f't = {t}'
            if is_active:
                board_lines.insert(0, color.GREEN + st(header_info, self.single_board_width) + color.END)
            else:
                board_lines.insert(0, st(header_info, self.single_board_width))

        board_string = '\n'.join(board_lines)

        if print_to_output:
            print(board_string)
        return(board_lines)

    def print_board_horizontally(self, highlight_t = -1, track_stone_ID = -1):
        # Causally free stones are BOLD
        # if highlight_t selected, the corresponding board is in GREEN
        total_board_lines = self.print_board_at_time(0, print_to_output = False, include_header_line = True, is_active = (highlight_t == 0), track_stone_ID = track_stone_ID)
        for t in range(1, self.t_dim):
            cur_board_lines = self.print_board_at_time(t, print_to_output = False, include_header_line = True, is_active = (highlight_t == t), track_stone_ID = track_stone_ID)
            for i in range(len(cur_board_lines)):
                total_board_lines[i] += self.board_delim + cur_board_lines[i]
        board_string = '\n'.join(total_board_lines)
        print(board_string)
        print("-" * self.header_width)

    def print_stone_list(self):
        for faction in self.factions:
            print(f"Player {faction} controls the following stones:")
            for stone_ID in self.faction_armies[faction]:
                msg = "  -" + str(self.stones[stone_ID])
                if stone_ID in self.stone_inheritance.keys():
                    msg += f" [Time-travels to become {str(self.stones[self.stone_inheritance[stone_ID]])}]"
                print(msg)

    def print_time_portals(self, t, x, y):
        TJI_active = []
        TJI_inactive = []
        TJO_active = []
        TJO_inactive = []
        # Of course, we look for TJIs one time-slice before.
        if t > 0:
            tji_square = self.board_dynamic[t-1][x][y]
        else:
            tji_square = self.setup_squares[x][y]
        for flag_ID in tji_square.flags:
            if self.flags[flag_ID].flag_type == "time_jump_in":
                if self.flags[flag_ID].flag_args[0]:
                    TJI_active.append(flag_ID)
                else:
                    TJI_inactive.append(flag_ID)
        for flag_ID in self.board_dynamic[t][x][y].flags:
            if self.flags[flag_ID].flag_type == "time_jump_out":
                if flag_ID in self.timejump_bijection.values():
                    TJO_active.append(flag_ID)
                else:
                    TJO_inactive.append(flag_ID)

        if len(TJI_active) + len(TJI_inactive) + len(TJO_active) + len(TJO_inactive) == 0:
            print(f"The square at ({t},{x},{y}) contains no time-jumps.")
        else:
            print(f"The square at ({t},{x},{y}) contains the following time-jumps:")
            if len(TJI_active) > 0:
                print("  Active time-jumps-in:")
                for flag_ID in TJI_active:
                    print(f"    -Portal ID {flag_ID}: A {str(self.stones[self.flags[flag_ID].stone_ID])} jumps in.")
            if len(TJI_inactive) > 0:
                print("  Inactive time-jumps-in:")
                for flag_ID in TJI_inactive:
                    print(f"    -Portal ID {flag_ID}: A {str(self.stones[self.flags[flag_ID].stone_ID])} would jump in.")
            if len(TJO_active) > 0:
                print("  Used time-jumps-out:")
                for flag_ID in TJO_active:
                    print(f"    -Portal ID {flag_ID}: A {str(self.stones[self.flags[flag_ID].stone_ID])} jumps out.")
            if len(TJO_inactive) > 0:
                print("  Unused time-jumps-out:")
                for flag_ID in TJO_inactive:
                    print(f"    -Portal ID {flag_ID}: A {str(self.stones[self.flags[flag_ID].stone_ID])} would jump out.")

    def print_stone_tracking(self, identifier):
        # The identifier may either be a stone ID or a position at which the stone is placed.
        stone_ID = None
        if isinstance(identifier, STPos):
            if self.board_dynamic[identifier.t][identifier.x][identifier.y].occupied:
                stone_ID = self.board_dynamic[identifier.t][identifier.x][identifier.y].stones[0]
            else:
                print("The identified square is unoccupied.")
        elif isinstance(identifier, int):
            stone_ID = identifier
        if stone_ID != None:
            print(f"Tracking the {str(self.stones[stone_ID])}...")
            self.print_board_horizontally(track_stone_ID = stone_ID)
            if stone_ID in self.stone_inheritance.values():
                # TJId
                for tji_ID in self.tji_ID_list:
                    if self.flags[tji_ID].stone_ID == stone_ID:
                        tjo_flag_ID = self.timejump_bijection[tji_ID]
                        print(f"The stone time-jumped-in at ({self.flags[tji_ID].pos.t + 1}, {self.flags[tji_ID].pos.x}, {self.flags[tji_ID].pos.y}) [Flag ID {tji_ID}], becoming a new version of {str(self.stones[self.flags[tjo_flag_ID].stone_ID])}")
                        break
            if stone_ID in self.stone_inheritance.keys():
                # TJOd
                for t in range(self.t_dim - 1, -1, -1):
                    if self.stones[stone_ID].history[t] != None:
                        last_x, last_y, last_a = self.stones[stone_ID].history[t]
                        for flag_ID in self.board_dynamic[t][last_x][last_y].flags:
                            if self.flags[flag_ID].flag_type == "time_jump_out" and self.flags[flag_ID].stone_ID == stone_ID:
                                print(f"The stone time-jumped-out at ({t}, {last_x}, {last_y}) [Flag ID {flag_ID}], changing into {str(self.stones[self.stone_inheritance[stone_ID]])}")
                                break


    # ----------------------------------------------------
    # ----------- board manipulation functions -----------
    # ----------------------------------------------------

    # static board functions

    def is_square_available(self, x, y):
        return(self.board_static[x][y] in [' '])

    # board access

    def clear_board(self):
        # This function removes all information about Board_square occupancy,
        # except for flags and stone dictionaries

        for t in range(self.t_dim):
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    self.board_dynamic[t][x][y].remove_stones()

    def place_stone_on_board(self, pos, stone_ID, stone_properties):
        # If the square is already occupied or unavailable, we track the square in a list of conflicting squares
        if self.board_dynamic[pos.t][pos.x][pos.y].occupied or (not self.is_square_available(pos.x, pos.y)):
            self.conflicting_squares[pos.t].append((pos.x,pos.y))
        self.board_dynamic[pos.t][pos.x][pos.y].add_stone(stone_ID, stone_properties)

    def remove_stone_from_game(self, stone_ID):
        # This is only relevant on undoing a stone-generating flag. Just a complete purge of that stone
        self.faction_armies[self.stones[stone_ID].player_faction].remove(stone_ID)
        del self.stones[stone_ID]

    def change_stone_pos(self, stone_ID, t, old_x, old_y, new_x, new_y):
        if not stone_ID in self.board_dynamic[t][old_x][old_y].stones:
            print(f"Error: Gamemaster.change_stone_pos attempted to move stone {stone_ID} from ({t},{old_x},{old_y}), where it currently isn't.")
            return(-1)
        self.board_dynamic[t][new_x][new_y].add_stone(stone_ID, self.board_dynamic[t][old_x][old_y].stone_properties[stone_ID])
        self.board_dynamic[t][old_x][old_y].remove_stone(stone_ID)

    # -------------- Flag management
    # Methods which add new Flags always return the Flag ID

    def remove_flag_from_game(self, flag_ID):
        flag_pos = self.flags[flag_ID].pos
        # First: If this is a stone generating flag type, we need to remove the generated stone
        if self.flags[flag_ID].flag_type in Flag.stone_generating_flag_types:
            self.remove_stone_from_game(self.flags[flag_ID].stone_ID)
        # Second: Remove flag from its board square
        if flag_pos.t == -1:
            self.setup_squares[flag_pos.x][flag_pos.y].remove_flag(flag_ID)
        else:
            self.board_dynamic[flag_pos.t][flag_pos.x][flag_pos.y].remove_flag(flag_ID)
        # Third: Purge the flag
        del self.flags[flag_ID]
        # Fourth: Remove flag from trackers
        if flag_ID in self.tji_ID_list:
            self.tji_ID_list.remove(flag_ID)
        if flag_ID in self.tji_ID_buffer.keys():
            # Removal of a newly added TJI also means removal of its associated TJO
            del self.tji_ID_buffer[flag_ID]

    def add_flag_spatial_move(self, stone_ID, t, old_x, old_y, new_x, new_y, new_a):
        new_flag = Flag(STPos(t, old_x, old_y), "spatial_move", self.stones[stone_ID].player_faction, [new_x, new_y, new_a], stone_ID)
        self.board_dynamic[t][old_x][old_y].add_flag(new_flag.flag_ID, stone_ID)
        self.flags[new_flag.flag_ID] = new_flag
        return(new_flag.flag_ID)

    def add_flag_attack(self, stone_ID, t, x, y, allow_friendly_fire):
        new_flag = Flag(STPos(t, x, y), "attack", self.stones[stone_ID].player_faction, [allow_friendly_fire], stone_ID)
        self.board_dynamic[t][x][y].add_flag(new_flag.flag_ID, stone_ID)
        self.flags[new_flag.flag_ID] = new_flag
        return(new_flag.flag_ID)

    def add_flag_timejump(self, stone_ID, old_t, old_x, old_y, new_t, new_x, new_y, new_a, adopted_stone_ID = -1):

        # If adopted_stone_ID specified, instead of creating a new TJI, we adopt an existing one.
        if adopted_stone_ID == -1:
            # The TJI is placed inactive, and may be activated during causal consistency resolution
            tji_flag = Flag(STPos(new_t - 1, new_x, new_y), "time_jump_in", self.stones[stone_ID].player_faction, [False, new_a])
            tjo_flag = Flag(STPos(old_t, old_x, old_y), "time_jump_out", self.stones[stone_ID].player_faction, [STPos(new_t - 1, new_x, new_y), tji_flag.flag_ID], stone_ID)

            # We place the flags.
            # The time_jump_in flag is actually placed one t lower than specified (-1 is allowed!), so the child can be controlled on the same time-slice it is placed onto.
            self.board_dynamic[old_t][old_x][old_y].add_flag(tjo_flag.flag_ID, stone_ID)
            if new_t - 1 >= 0:
                self.board_dynamic[new_t - 1][new_x][new_y].add_flag(tji_flag.flag_ID, tji_flag.stone_ID)
            if new_t == 0:
                # We place the flag into a special time-slice
                self.setup_squares[new_x][new_y].add_flag(tji_flag.flag_ID, tji_flag.stone_ID)
            self.flags[tjo_flag.flag_ID] = tjo_flag
            self.flags[tji_flag.flag_ID] = tji_flag

            # Trackers
            self.tji_ID_buffer[tji_flag.flag_ID] = tjo_flag.flag_ID

            # We add the new stone into the army
            self.stones[tji_flag.stone_ID] = Stone(tji_flag.stone_ID, self.stones[stone_ID].player_faction, self.t_dim)
            self.faction_armies[self.stones[stone_ID].player_faction].append(tji_flag.stone_ID)
            return([tjo_flag.flag_ID, tji_flag.flag_ID])
        else:
            # First, we find the TJI which summons the stone
            adopted_stone_found = False
            for tji_ID in self.tji_ID_list:
                if self.flags[tji_ID].stone_ID == adopted_stone_ID:
                    adopted_stone_found = True
                    # We now check if it is allowed to link us up
                    if not (self.flags[tji_ID].pos.t == new_t - 1 and self.flags[tji_ID].pos.x == new_x and self.flags[tji_ID].pos.y == new_y):
                        return("except Specified stone doesn't time-jump-in at the specified square")
                    if self.stones[stone_ID].player_faction != self.stones[adopted_stone_ID].player_faction:
                        return("except Specified stone belongs to a different faction")
                    if self.stones[stone_ID].stone_type not in ["wildcard", self.stones[adopted_stone_ID].stone_type]:
                        return("except Specified stone is of a different type")
                    if self.flags[tji_ID].flag_args[1] != new_a:
                        return("except Specified stone jumps in at a different azimuth than proposed")
                    # We can link up!
                    tjo_flag = Flag(STPos(old_t, old_x, old_y), "time_jump_out", self.stones[stone_ID].player_faction, [STPos(new_t - 1, new_x, new_y), tji_ID], stone_ID)
                    self.board_dynamic[old_t][old_x][old_y].add_flag(tjo_flag.flag_ID, stone_ID)
                    self.flags[tjo_flag.flag_ID] = tjo_flag
                    return([tjo_flag.flag_ID])

            if not adopted_stone_found:
                return("except Specified stone not linked with a time-jump-in")


    def set_tji_activity(self, tji_ID, new_is_active):
        """tji_pos = self.flag_index[tji_ID]
        if tji_pos.t == -1:
            old_arguments = self.setup_squares[tji_pos.x][tji_pos.y].get_flag_arguments(tji_ID)
            old_arguments[0] = new_is_active
            self.setup_squares[tji_pos.x][tji_pos.y].set_flag_arguments(tji_ID, old_arguments)
        else:
            old_arguments = self.board_dynamic[tji_pos.t][tji_pos.x][tji_pos.y].get_flag_arguments(tji_ID)
            old_arguments[0] = new_is_active
            self.board_dynamic[tji_pos.t][tji_pos.x][tji_pos.y].set_flag_arguments(tji_ID, old_arguments)"""
        self.flags[tji_ID].flag_args[0] = new_is_active


    def resolve_conflicts(self, t):
        # Resolves conflicts in a specified time-slice
        # Assumes all previous time-slices are canonical (void of conflicts)
        # The paradigm here is as follows: 1 Sokoban; 2 Impasse; 3 Destruction

        # 1 Sokoban
        # Sokoban pushes do not occur at t = 0, as they depend on the state of the board in the previous time-slice
        if t != 0:
            squares_to_be_checked = self.conflicting_squares[t].copy()

            while(len(squares_to_be_checked) > 0):
                cur_pos = squares_to_be_checked.pop(0)
                x, y = cur_pos
                if len(self.board_dynamic[t][x][y].stones) != 2:
                    continue
                # Sokoban pushes cannot occur through walls
                if not self.is_square_available(x, y):
                    continue
                stone_a = self.board_dynamic[t][x][y].stones[0]
                stone_b = self.board_dynamic[t][x][y].stones[1]
                # We check if one stone was already present here on the previous time-slice and the other moved in spatially
                if self.stones[stone_a].history[t-1] == None or self.stones[stone_b].history[t-1] == None:
                    continue
                prev_x_a, prev_y_a, prev_a_a = self.stones[stone_a].history[t-1]
                prev_x_b, prev_y_b, prev_a_b = self.stones[stone_b].history[t-1]
                # Sokoban push only occurs if the moving stone moved by distance 1 in one of the four cardinal directions
                if prev_x_a == x and prev_y_a == y:
                    # First stone was waiting
                    b_delta = get_azimuth_from_delta_pos((prev_x_b, prev_y_b), (x, y))
                    if b_delta != -1:
                        # Sokoban push can occur!
                        new_pos_x, new_pos_y = pos_step((x, y), b_delta)
                        if self.is_square_available(new_pos_x, new_pos_y) and not self.board_dynamic[t][new_pos_x][new_pos_y].occupied:
                            #self.board_dynamic[t][new_pos_x][new_pos_y].add_stone(stone_a, self.board_dynamic[t][x][y].stone_properties[stone_a])
                            #self.board_dynamic[t][x][y].remove_stone(stone_a)
                            self.change_stone_pos(stone_a, t, x, y, new_pos_x, new_pos_y)
                            # We remove the conflict
                            self.conflicting_squares[t].remove((x, y))
                if prev_x_b == x and prev_y_b == y:
                    # Second stone was waiting
                    a_delta = get_azimuth_from_delta_pos((prev_x_a, prev_y_a), (x, y))
                    if a_delta != -1:
                        # Sokoban push can occur!
                        new_pos_x, new_pos_y = pos_step((x, y), a_delta)
                        if self.is_square_available(new_pos_x, new_pos_y) and not self.board_dynamic[t][new_pos_x][new_pos_y].occupied:
                            #self.board_dynamic[t][new_pos_x][new_pos_y].add_stone(stone_b, self.board_dynamic[t][x][y].stone_properties[stone_b])
                            #self.board_dynamic[t][x][y].remove_stone(stone_b)
                            self.change_stone_pos(stone_b, t, x, y, new_pos_x, new_pos_y)
                            # We remove the conflict
                            self.conflicting_squares[t].remove((x, y))

        # 2 Opposition
        # Opposition do not occur at t = 0, as they depend on the state of the board in the previous time-slice
        if t != 0:
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    for one_ID in self.board_dynamic[t][x][y].stones:
                        if not self.stones[one_ID].opposable:
                            continue
                        old_pos = self.stones[one_ID].history[t-1]
                        if old_pos == None:
                            continue
                        old_x, old_y, old_a = old_pos
                        if old_x == x and old_y == y:
                            # No movement happened
                            continue
                        for two_ID in self.board_dynamic[t][old_x][old_y].stones:
                            if not self.stones[two_ID].opposable:
                                continue
                            two_old_pos = self.stones[two_ID].history[t-1]
                            if two_old_pos == None:
                                continue
                            two_old_x, two_old_y, two_old_a = two_old_pos
                            if x == two_old_x and y == two_old_y:
                                # Opposition
                                self.change_stone_pos(one_ID, t, x, y, old_x, old_y)
                                self.change_stone_pos(two_ID, t, old_x, old_y, x, y)
                                break

        # 3 Impasse
        # Impasses do not occur at t = 0, as they depend on the state of the board in the previous time-slice
        if t != 0:
            # Since this rule chains, it will keep adding to squares_to_be_checked according to need. Stones which are returned back through an impasse or cannot be returned are tracked in stones_checked,
            # and the impasse checking stops once all conflicting squares are occupied only by stones present in stones_checked
            squares_to_be_checked = self.conflicting_squares[t].copy()
            stones_checked = []
            while(len(squares_to_be_checked) > 0):
                cur_pos = squares_to_be_checked.pop(0)
                x, y = cur_pos
                # We take all the stones present, add them to the stones_checked tracker, and move those which existed in the previous time-slice back
                # If we move them back into an occupied square, that square is naturally added to squares_to_be_checked AND to self.conflicting_squares
                stones_on_current_square = self.board_dynamic[t][x][y].stones.copy()
                for cur_ID in stones_on_current_square:
                    if cur_ID in stones_checked:
                        # The stone has already been moved back
                        continue
                    stones_checked.append(cur_ID)
                    previous_pos = self.stones[cur_ID].history[t-1]
                    if previous_pos == None:
                        # The stone was just added onto the board.
                        continue
                    prev_x, prev_y, prev_a = previous_pos
                    if prev_x == x and prev_y == y:
                        # The stone was waiting in the previous time-slice, and is not to be moved.
                        continue
                    # We move the stone back. If the previous square is occupied or unavailable, we add it to squares_to_be_checked
                    if self.board_dynamic[t][prev_x][prev_y].occupied or (not self.is_square_available(prev_x, prev_y)):
                        if not (prev_x, prev_y) in squares_to_be_checked:
                            squares_to_be_checked.append((prev_x, prev_y))
                        if not (prev_x, prev_y) in self.conflicting_squares[t]:
                            self.conflicting_squares[t].append((prev_x, prev_y))
                    self.change_stone_pos(cur_ID, t, x, y, prev_x, prev_y)
                # We check if the square is no longer conflicting. If not, we remove it from self.conflicting_squares[t]
                if self.is_square_available(x, y):
                    if len(self.board_dynamic[t][x][y].stones) < 2:
                        self.conflicting_squares[t].remove(cur_pos)
                elif not self.board_dynamic[t][x][y].occupied:
                    self.conflicting_squares[t].remove(cur_pos)

        # 4 Explosion
        # We remove all stones from all remaining conflicting squares
        while(len(self.conflicting_squares[t]) > 0):
            cur_pos = self.conflicting_squares[t].pop(0)
            x, y = cur_pos
            self.board_dynamic[t][x][y].remove_stones()

    # Temporal resolution algorithms

    def resolve_causal_consistency(self):
        # The wrapper for causal consistency methods

        # Order setup stones by a deterministic criterion from least prioritised to most prioritised
        active_setup_stones = list(self.setup_stones.keys())

        # The ordering cannot be added on the TUI but this is how it's gonna work:
        # Every time a player selects a setup stone and adds a flag to it, it floats down to
        # the end of the ordered list. Hence, after a turn, the stones are ordered from
        # first-commanded (least priority to keep) to last-commanded (biggest priority to keep).
        # The philosophy is: "The more recently you've touched a stone, the bigger the chance
        # it will survive a paradox."
        # Naturally, stones which become causally locked are not touched and become low priority,
        # and hence will be removed first.
        ordered_setup_stones = active_setup_stones #TODO

        for number_of_deactivations in range(len(active_setup_stones) + 1):
            activity_maps = ordered_switch_flips(len(active_setup_stones), number_of_deactivations) # True means deactivate
            for activity_map in activity_maps:
                # We set active add_stone flags according to current activity map
                for i in range(len(active_setup_stones)):
                    self.flags[self.setup_stones[ordered_setup_stones[i]]].flag_args[0] = not activity_map[i]

                # We find all causally consistent scenarios for this activity map
                causally_consistent_scenarios = self.find_causally_consistent_scenarios()
                if len(causally_consistent_scenarios) == 0:
                    continue # Paradox
                else:
                    # We commit to the canonical scenario
                    canonical_scenario = self.select_scenario(causally_consistent_scenarios.copy())
                    for i in range(len(self.tji_ID_list)):
                        # We set the is_active argument according to the activity map
                        self.set_tji_activity(self.tji_ID_list[i], canonical_scenario[i])

                    # We delete all inactive setup stones from self.setup_stones,
                    # disallowing them from being considered for activation later.

                    recently_removed_setup_stones = []

                    for i in range(len(activity_map)):
                        self.removed_setup_stones[ordered_setup_stones[i]] = self.setup_stones[ordered_setup_stones[i]]
                        recently_removed_setup_stones.append(ordered_setup_stones[i])
                        del self.setup_stones[ordered_setup_stones[i]]

                    return(Message("removed stones", recently_removed_setup_stones))

        # If we get to this point, something has gone terribly wrong, as not even
        # the removal of all stones yielded a causally consistent scenario

        # This should theoretically never occur, as deactivating all add_stone flags
        # AND all TJIs should result in a completely empty board, which is always causally consistent.
        return(Message("exception"), "Unable to find a causally consistent scenario.")



    def find_causally_consistent_scenarios(self):
        # takes the internal timejump surjection and returns a list of activity maps, where each activity map is a list of booleans,
        # where the i-th element specifies if the i-th TJI (ordered by flag_ID) should be active.

        # A causally consistent scenario is one such that
        #   -For every in-active TJI, no stone reaches any corresponding TJO
        #   -For every active TJI, exactly one stone reaches a corresponding TJO

        causally_consistent_scenarios = []
        tji_N = len(self.tji_ID_list)
        if tji_N == 0:
            return([[]]) # The only possible scenario is also, by design, causally consistent

        activity_map = [False] * tji_N

        for n in range(int(np.power(2, tji_N))):
            # first, prepare the moves
            how_many_TJOs_required = {}
            for i in range(tji_N):
                # We set the is_active argument according to the activity map
                self.set_tji_activity(self.tji_ID_list[i], activity_map[i])
                if activity_map[i] == True:
                    how_many_TJOs_required[self.tji_ID_list[i]] = 1
                if activity_map[i] == False:
                    how_many_TJOs_required[self.tji_ID_list[i]] = 0
            # execute them
            self.execute_moves(reset_timejump_trackers = True)
            # Now we just compare self.tji_bearing to how_many_TJOs_required
            is_scenario_causally_consistent = True
            for tji_ID in self.tji_ID_list:
                if how_many_TJOs_required[tji_ID] != self.tji_bearing[tji_ID]:
                    is_scenario_causally_consistent = False
                    break
            if is_scenario_causally_consistent:
                causally_consistent_scenarios.append(activity_map.copy())

            # find the next activity map
            for i in range(tji_N):
                if activity_map[i] == False:
                    activity_map[i] = True
                    break
                else:
                    activity_map[i] = False
        return(causally_consistent_scenarios)

    def select_scenario(self, causally_consistent_scenarios):
        # THE PARADIGM HERE: We prioritize more recent TJIs to be active: the bigger the associated tji flag ID, the earlier will this break a tie
        if len(causally_consistent_scenarios) == 1:
            return(causally_consistent_scenarios[0])
        tji_N = len(self.tji_ID_list)
        for i in range(tji_N - 1, -1, -1):
            if len(causally_consistent_scenarios) == 1:
                return(causally_consistent_scenarios[0])
            is_TJI_filtering = False
            first_val = causally_consistent_scenarios[0][i]
            for j in range(1, len(causally_consistent_scenarios)):
                if causally_consistent_scenarios[j][i] != first_val:
                    is_TJI_filtering = True
                    break
            if is_TJI_filtering:
                # we delete all the scenarios that turn set TJI inactive
                j = 0
                while(j < len(causally_consistent_scenarios)):
                    if causally_consistent_scenarios[j][i] == False:
                        causally_consistent_scenarios.pop(j)
                    else:
                        j += 1
        print("The causally_consistent_scenarios list obviously wasn't sane, please check the remainder:")
        print(causally_consistent_scenarios)
        print("Returning the first element...")
        return(causally_consistent_scenarios[0])





    def execute_moves(self, reset_timejump_trackers = False):
        # This function populates Board_squares with stones according to all flags

        # First, we clear the board
        self.clear_board()
        if reset_timejump_trackers:
            self.tji_bearing = {}
            self.timejump_bijection = {}
            self.stone_inheritance = {}
            for tji_ID in self.tji_ID_list:
                self.tji_bearing[tji_ID] = 0

        # Then, we execute setup flags, i.e. initial stone creation
        for x in range(self.x_dim):
            for y in range(self.y_dim):
                for cur_flag_ID in self.setup_squares[x][y].flags:
                    cur_flag = self.flags[cur_flag_ID]
                    if cur_flag.flag_type == "add_stone":
                        if cur_flag.flag_args[0]:
                            self.board_dynamic[0][x][y].add_stone(cur_flag.stone_ID, [cur_flag.flag_args[1]])
                    if cur_flag.flag_type == "time_jump_in":
                        if cur_flag.flag_args[0]:
                            self.board_dynamic[0][x][y].add_stone(cur_flag.stone_ID, [cur_flag.flag_args[1]])

        # Then, we execute flags for each time slice sequantially
        for t in range(self.t_dim):
            # At t, we are treating the state of the board at t as canonical, and we use it to
            # calculate the state of the board at t + 1. We do this by first naively resolving
            # the flags at t and then executing a conflict resolution routine which reverts
            # moves which result in conflict.


            # Conflict resolution
            self.resolve_conflicts(t)

            # At this moment, the time-slice t is in its canonical state, and stone history may be recorded
            recorded_stones = []
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    if self.board_dynamic[t][x][y].occupied:
                        self.stones[self.board_dynamic[t][x][y].stones[0]].history[t] = (x, y, self.board_dynamic[t][x][y].stone_properties[self.board_dynamic[t][x][y].stones[0]][0])
                        recorded_stones.append(self.board_dynamic[t][x][y].stones[0])
            # All stones not recorded are set to position None
            for cur_ID in self.stones.keys():
                if not cur_ID in recorded_stones:
                    self.stones[cur_ID].history[t] = None

            # Naive flag execution
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    for cur_flag_ID in self.board_dynamic[t][x][y].flags:
                        cur_flag = self.flags[cur_flag_ID]
                        # Flag switch here

                        # These flags propagate the stone into the next time-slice, and as such are forbidden at t = self.t_dim - 1
                        # If a stone is propagated onto an occupied square, the square is added to self.conflicting_squares
                        if t < self.t_dim - 1:
                            if cur_flag.flag_type == "add_stone":
                                if cur_flag.flag_args[0]:
                                    self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                            if cur_flag.flag_type == "time_jump_in":
                                if cur_flag.flag_args[0]:
                                    self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                            # For the following flags, the stone has to be present in the current time-slice
                            if cur_flag.stone_ID in self.board_dynamic[t][x][y].stones:
                                if cur_flag.flag_type == "spatial_move":
                                    self.place_stone_on_board(STPos(t+1, cur_flag.flag_args[0], cur_flag.flag_args[1]), cur_flag.stone_ID, [cur_flag.flag_args[2]])
                                if cur_flag.flag_type == "attack":
                                    self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, self.board_dynamic[t][x][y].stone_properties[cur_flag.stone_ID])
                                    # TODO resolve attack here
                        # The following flags remove the stone from the board, and as such are the only flags which can be placed at t = t_dim - 1
                        if cur_flag.stone_ID in self.board_dynamic[t][x][y].stones:
                            if cur_flag.flag_type == "time_jump_out":
                                # If TJO was newly added (still in the buffer), it shouldn't update trackers
                                if reset_timejump_trackers and cur_flag.flag_ID not in self.tji_ID_buffer.values():
                                    self.tji_bearing[cur_flag.flag_args[1]] += 1
                                    self.timejump_bijection[cur_flag.flag_args[1]] = cur_flag.flag_ID
                                    self.stone_inheritance[cur_flag.stone_ID] = self.flags[cur_flag.flag_args[1]].stone_ID








    # ----------------------------------------------------
    # --------------- game loop functions ----------------
    # ----------------------------------------------------

    def causally_free_stones_at_time(self, t):
        causally_free_armies = {}
        for faction in self.factions:
            causally_free_armies[faction] = []

        for x in range(self.x_dim):
            for y in range(self.y_dim):
                for causally_free_stone_ID in self.board_dynamic[t][x][y].causally_free_stones:
                    causally_free_armies[self.stones[causally_free_stone_ID].player_faction].append(causally_free_stone_ID)
        return(causally_free_armies)

    def standard_game_loop(self):

        self.round_number = -1
        self.current_time = 0

        while(True):
            self.round_number += 1
            self.print_heading_message(f"Round {self.round_number} commences", 0)

            for self.current_time in range(self.t_dim):
                # First, we find the canonical state of the board
                self.execute_moves()

                # Second, we display the board state
                self.print_heading_message(f"Time = {self.current_time}", 1)
                self.print_board_horizontally(self.current_time)

                # Third, for every causally free stone, we ask its owner to place a flag
                currently_causally_free_stones = self.causally_free_stones_at_time(self.current_time)
                for player in self.factions:
                    self.print_heading_message(f"Player {player}, it is your turn to command your stones now.", 2)
                    if len(currently_causally_free_stones[player]) == 0:
                        self.print_heading_message("No causally free stones to command.", 3)
                    stone_index = 0
                    flags_added_this_turn = repeated_list(len(currently_causally_free_stones[player]), None)
                    while(stone_index < len(currently_causally_free_stones[player])):
                        cur_stone = currently_causally_free_stones[player][stone_index]
                        cur_pos = self.stones[cur_stone].history[self.current_time]
                        x, y, a = cur_pos
                        self.print_heading_message(f"Command your stone at ({x},{y}).", 3)
                        if self.current_time < self.t_dim - 1:
                            move_msg = self.stones[cur_stone].parse_move_cmd(self, self.current_time)
                        else:
                            move_msg = self.stones[cur_stone].parse_final_move_cmd(self, self.current_time)
                        if move_msg == "quit":
                            return(-1)
                        if move_msg == "undo":
                            # We revert back to the previous stone
                            stone_index = max(stone_index-1, 0)
                            # We delete the Flag we added to this stone if any
                            if flags_added_this_turn[stone_index] != None:
                                prev_x, prev_y, prev_a = self.stones[currently_causally_free_stones[player][stone_index]].history[self.current_time]
                                for added_flag_ID in flags_added_this_turn[stone_index]:
                                    self.remove_flag_from_game(added_flag_ID)
                                    #self.board_dynamic[self.current_time][prev_x][prev_y].remove_flag()
                            continue

                        move_msg_split = move_msg.split(" ")
                        if move_msg_split[0] == "flag_added":
                            # A new Flag was added
                            flags_added_for_stone = []
                            for i in range(1, len(move_msg_split)):
                                flags_added_for_stone.append(int(move_msg_split[i]))
                            flags_added_this_turn[stone_index] = flags_added_for_stone

                        stone_index += 1

            # ---------------------- Sorting out time travel --------------------------

            # We have now spanned the entire temporal length of the board, and must now select a causally consistent scenario
            self.print_heading_message("Selecting a causally-consistent scenario", 1)
            causally_consistent_scenarios = self.find_causally_consistent_scenarios()
            if len(causally_consistent_scenarios) == 0:
                # And just like that, we have reached a paradoxical situation. What now?
                self.print_heading_message("A paradox has been reached!", 2)
            canonical_scenario = self.select_scenario(causally_consistent_scenarios.copy())
            for i in range(len(self.tji_ID_list)):
                # We set the is_active argument according to the activity map
                self.set_tji_activity(self.tji_ID_list[i], canonical_scenario[i])

            # We now set all newly added TJIs as active and flush tji_ID_buffer into tji_ID_list. We update the trackers.
            for new_tji_ID, new_tjo_ID in self.tji_ID_buffer.items():
                self.set_tji_activity(new_tji_ID, True)
                self.tji_ID_list.append(new_tji_ID)
                self.timejump_bijection[new_tji_ID] = new_tjo_ID
                self.stone_inheritance[self.flags[new_tjo_ID].stone_ID] = self.flags[new_tji_ID].stone_ID

            self.tji_ID_buffer = {}



