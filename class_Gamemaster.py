

import math

import constants

from functions import *
from class_STPos import STPos
from class_Message import Message
from class_Scenario import Scenario

# Import the stone types
from class_Stone import Stone
from class_Tank import Tank
from class_Bombardier import Bombardier

from class_Flag import Flag
from class_Board_square import Board_square

# -----------------------------------------------------------------------------
# ----------------------------- class Gamemaster ------------------------------
# -----------------------------------------------------------------------------

class Gamemaster():

    # -------------------------------------------------------------------------
    # ---------------- constructors, destructors, descriptors -----------------
    # -------------------------------------------------------------------------

    def __init__(self, display_logs = False):

        self.display_logs = display_logs

        self.print_log("Initialising game trackers and memory bins...",)

        # Stone trackers. The lists are updated when flags are placed, and do not depend on which stones are actually present on the board dynamically.
        self.stones = {} #[ID] = Stone()
        self.faction_armies = {} #[faction] = [ID_1, ID_2 ... ]
        self.factions = ['A', 'B']
        self.stone_causal_freedom = {} # [stone_ID] = timeslice of causal freedom OR None if stone is not free/not on the board. NOTE: updated ONLY by execute_moves()
        # Setup trackers
        self.setup_stones = {} # Tracker for stones which are added on board setup. This is used when resolving paradoxes. [stone_ID] = flag_ID
        self.removed_setup_stones = {} # [stone_ID] = flag_ID

        # Actions. These are queued by waiting flags and flushed in execute_moves.
        self.stone_actions = [] # [t][stone_ID] = flag_ID which initiated action
        self.board_actions = [] # [t][x][y]["board action"] = True or False
        self.available_board_actions = [ # This is just a reference list, and should not be changed
                "destruction",  # destroys stone at position if exists
                "explosion",    # destroys stones at position and adjanced positions if exist
                "tagscreen"     # tags stones at position and adjanced positions as unable to travel back in time
            ]

        # the board
        self.board_static = [] # [x][y] = type
        self.board_dynamic = [] # [t][x][y] = Board_square
        self.conflicting_squares = [] # [t] = (x,y) of a board square which is occupied by more than one stone at time t
        self.setup_squares = [] # this acts as board_dynamic with t = -1, and only accepts stone creating flags

        # flags
        self.flags = {} # [flag_ID] = Flag()
        self.flags_by_turn = [] # [turn_number]["faction"] = [list of flag IDs added by that player that turn]
        # flags_by_turn is never handled by the add_flag methods, as they are turn-number-invariant. Instead,
        # it is always handled by the input prompt (loader or player input).

        # ----------------------- Game status variables -----------------------
        self.current_turn_index = None # Index of turn where some or all players need to add commands

        # ------------------ Trackers for reverse causality -------------------
        # General trackers
        self.effects_by_round = [] # [round number] = [flags which are effected from a later timeslice added in specific round]
        self.effect_load = {} # [effect ID] = number of activated causes
        self.effect_cause_map = {} # [effect ID] = cause ID for active effects
        # Convenience trackers
        self.stone_inheritance = {} # [stone_ID] = child_ID

        self.scenarios_by_round = [] # [round_number] = Scenario(activity maps, trackers)

        # TUI elements
        self.board_delim = ' | '


        # ---------------------------------------------------------------
        # ------------------- Saving and loading game -------------------
        # ---------------------------------------------------------------
        # An instance of Gamemaster is created freshly whenever the Game
        # url is loaded. From the unique Game ID, the appropriate data
        # from the server-side db are loaded into this instance, and the
        # game is brought to the latest state, where the user can inter-
        # act with the Gamemaster to create a new datum to be sent to
        # server-side.
        # The data is in the following form:
        #   1. Static data: Data about the board, which doesn't depend on
        #      the state of the specific Game. This is in the format of
        #      [t_dim, x_dim, y_dim, board representation]
        #      (Note that setup moves are copied into table Games for
        #      each new instance, as that table has to contain all the
        #      flag creation data.)
        #   2. Dynamic data: All the other moves. Each move datum is ID'd
        #      by the Game, the Player (can be "GM", e.g. for setup
        #      moves), and the Index (starting from 0 for setup moves and
        #      incrementing sequentially). The content is a list of flags
        #      ordered by Flag ID (for stone causal priority), with the
        #      format being:
        #        "flag_ID,flag_type,player_faction,stone_ID,pos,args;..."
        #      where different flags are separated by ';' and the args
        #      for each flag are separated by ','.
        # The loading paradigm is as follows:
        #   1. Astatic board is initialized from the static data
        #      representation.
        #   2. For each move index:
        #     2.1. All the moves are placed as flags onto the board
        #     2.2. End-of-turn routine plays out (conflict resolution in
        #          the middle of a round, temporal consistency resolution
        #          at the end of a round, win condition check).
        # After that, the state of the board is displayed (and viewable
        # for any max_index) and the player is prompted for their input.

        # The following properties are the raw datapoints mirroring the
        # server-side db. They are both loaded from the db and updated by
        # user interaction

        self.static_representation = []
        # The full dynamic representation, for loading purposes
        self.dynamic_representation = [] #[move_index]["faction"] = "flag representations"
        # The staged commit dynamic representation, for saving purposes
        # (during save routine, the elements of this array are inserted into MOVES)
        # For old moves, the elements are empty dictionaries
        self.new_dynamic_representation = [] #[move_index]["faction"] = "flag representations"


    # -------------------------------------------------------------------------
    # ---------------------------- Print functions ----------------------------
    # -------------------------------------------------------------------------

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

    def print_board_at_time(self, round_n, t, print_to_output = True, include_header_line = False, is_active = False, track_stone_ID = -1):

        def print_stone(board_lines, stone_symbol, stone_position, stone_azimuth, is_orientable = False, is_causally_free = False, is_tracked = False):
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
            if is_orientable:
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
                    is_occupant_causally_free = (self.stone_causal_freedom[occupant_ID] == t)
                    stone_symbol = constants.stone_symbols[self.stones[occupant_ID].player_faction][self.stones[occupant_ID].stone_type]
                    print_stone(board_lines, stone_symbol, (x, y), self.board_dynamic[t][x][y].stone_properties[occupant_ID][0], is_orientable = self.stones[occupant_ID].orientable, is_causally_free = is_occupant_causally_free, is_tracked = (track_stone_ID == occupant_ID))

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
                for cur_flag_ID in TJI_square.all_flags:
                    if has_conflict:
                        break
                    if self.flags[cur_flag_ID].flag_type == "time_jump_in":
                        if cur_flag_ID in self.scenarios_by_round[round_n].effect_cause_map.keys():
                            # Active TJI
                            if has_active_TJI or has_active_TJO:
                                # Conflict!
                                has_conflict = True
                            has_active_TJI = True
                        else:
                            # Inactive TJI
                            has_inactive_TJI = True
                for cur_flag_ID in self.board_dynamic[t][x][y].all_flags:
                    if has_conflict:
                        break
                    if self.flags[cur_flag_ID].flag_type == "time_jump_out":
                        if cur_flag_ID in self.scenarios_by_round[round_n].effect_cause_map.values():
                            # Active TJO
                            if has_active_TJI or has_active_TJO:
                                # Conflict!
                                has_conflict = True
                            has_active_TJO = True
                        else:
                            # Inactive TJO
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

    def print_board_horizontally(self, active_turn, highlight_active_timeslice = False, track_stone_ID = -1):
        # Causally free stones are BOLD
        # if highlight_t selected, the corresponding board is in GREEN
        cur_round, cur_active_timeslice = self.round_from_turn(active_turn)
        total_board_lines = self.print_board_at_time(cur_round, 0, print_to_output = False, include_header_line = True, is_active = (cur_active_timeslice == 0 and highlight_active_timeslice), track_stone_ID = track_stone_ID)
        for t in range(1, self.t_dim):
            cur_board_lines = self.print_board_at_time(cur_round, t, print_to_output = False, include_header_line = True, is_active = (cur_active_timeslice == t and highlight_active_timeslice), track_stone_ID = track_stone_ID)
            for i in range(len(cur_board_lines)):
                total_board_lines[i] += self.board_delim + cur_board_lines[i]
        board_string = '\n'.join(total_board_lines)
        print(board_string)
        print("-" * self.header_width)

    def print_stone_list(self, which_round = None):
        if which_round is None:
            cur_round, _ = self.round_from_turn(self.current_turn_index)
            which_round = cur_round
        for faction in self.factions:
            print(f"Player {faction} controls the following stones:")
            for stone_ID in self.faction_armies[faction]:
                msg = "  -" + str(self.stones[stone_ID])
                if self.flags[self.stones[stone_ID].progenitor_flag_ID].is_active == False:
                    msg += f" [Not placed on the board to maintain causal consistency]"
                if stone_ID in self.scenarios_by_round[which_round].stone_inheritance.keys():
                    msg += f" [Time-travels to become {str(self.stones[self.scenarios_by_round[which_round].stone_inheritance[stone_ID]])}]"
                print(msg)

    def print_time_portals(self, t, x, y, which_round = None):
        if which_round is None:
            cur_round, _ = self.round_from_turn(self.current_turn_index)
            which_round = cur_round
        TJI_active = []
        TJI_inactive = []
        TJO_active = []
        TJO_inactive = []
        # Of course, we look for TJIs one time-slice before.
        if t > 0:
            tji_square = self.board_dynamic[t-1][x][y]
        else:
            tji_square = self.setup_squares[x][y]
        for flag_ID in tji_square.all_flags:
            if self.flags[flag_ID].flag_type == "time_jump_in":
                if self.flags[flag_ID].is_active:
                    TJI_active.append(flag_ID)
                else:
                    TJI_inactive.append(flag_ID)
        for flag_ID in self.board_dynamic[t][x][y].all_flags:
            if self.flags[flag_ID].flag_type == "time_jump_out":
                if flag_ID in self.scenarios_by_round[which_round].effect_cause_map.values():
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

    def print_stone_tracking(self, identifier, which_round = None):
        # The identifier may either be a stone ID or a position at which the stone is placed.
        # Which round: which round is it that we show this tracking.
        if which_round is None:
            cur_round, _ = self.round_from_turn(self.current_turn_index)
            which_round = cur_round
        stone_ID = None
        if isinstance(identifier, STPos):
            if self.board_dynamic[identifier.t][identifier.x][identifier.y].occupied:
                stone_ID = self.board_dynamic[identifier.t][identifier.x][identifier.y].stones[0]
            else:
                print("The identified square is unoccupied.")
                return(-1)
        elif isinstance(identifier, int):
            stone_ID = identifier
        if stone_ID not in self.stones.keys():
            print("The selected stone does not exist.")
            return(-1)
        if self.flags[self.stones[stone_ID].progenitor_flag_ID].is_active == False:
            print("The selected stone has not been placed on the board in the recently selected causally-consistent scenario.")
            return(-1)

        print(f"Tracking the {str(self.stones[stone_ID])}...")
        self.print_board_horizontally(active_turn = min(self.t_dim * (which_round + 1), self.current_turn_index), highlight_active_timeslice = False, track_stone_ID = stone_ID)
        if self.flags[self.stones[stone_ID].progenitor_flag_ID].flag_type == "add_stone":
            print(f"The stone has been placed on setup at ({self.flags[self.stones[stone_ID].progenitor_flag_ID].pos.t + 1}, {self.flags[self.stones[stone_ID].progenitor_flag_ID].pos.x}, {self.flags[self.stones[stone_ID].progenitor_flag_ID].pos.y}) [Flag ID {self.stones[stone_ID].progenitor_flag_ID}]")
        elif self.flags[self.stones[stone_ID].progenitor_flag_ID].flag_type == "time_jump_in":
            tjo_flag_ID = self.scenarios_by_round[which_round].effect_cause_map[self.stones[stone_ID].progenitor_flag_ID]
            print(f"The stone time-jumped-in at ({self.flags[self.stones[stone_ID].progenitor_flag_ID].pos.t + 1}, {self.flags[self.stones[stone_ID].progenitor_flag_ID].pos.x}, {self.flags[self.stones[stone_ID].progenitor_flag_ID].pos.y}) [Flag ID {self.stones[stone_ID].progenitor_flag_ID}], becoming a new version of {str(self.stones[self.flags[tjo_flag_ID].stone_ID])}")
        if stone_ID in self.scenarios_by_round[which_round].stone_inheritance.keys():
            # TJOd
            for t in range(self.t_dim - 1, -1, -1):
                if self.stones[stone_ID].history[t] != None:
                    last_x, last_y, last_a = self.stones[stone_ID].history[t]
                    for flag_ID in self.board_dynamic[t][last_x][last_y].all_flags:
                        if self.flags[flag_ID].flag_type == "time_jump_out" and self.flags[flag_ID].stone_ID == stone_ID:
                            print(f"The stone time-jumped-out at ({t}, {last_x}, {last_y}) [Flag ID {flag_ID}], changing into {str(self.stones[self.scenarios_by_round[which_round].stone_inheritance[stone_ID]])}")
                            break


    # -------------------------------------------------------------------------
    # --------------------- Board manipulation functions ----------------------
    # -------------------------------------------------------------------------

    # ------------------------ Static board functions -------------------------

    def is_square_available(self, x, y):
        if not self.is_valid_position(x, y):
            return(False)
        return(self.board_static[x][y] in [' '])

    def is_valid_position(self, x, y):
        if x >= 0 and x < self.x_dim and y >= 0 and y < self.y_dim:
            return(True)
        return(False)

    def get_adjanced_positions(self, x, y, number_of_steps):
        adjanced_positions = []
        for delta_x in range(number_of_steps + 1):
            for delta_y in range((number_of_steps - delta_x) + 1):
                if delta_x == 0 and delta_y == 0:
                    if self.is_valid_position(x, y):
                        adjanced_positions.append((x, y))
                    continue
                if self.is_valid_position(x + delta_x, y + delta_y):
                    adjanced_positions.append((x + delta_x, y + delta_y))
                if self.is_valid_position(x - delta_x, y + delta_y):
                    adjanced_positions.append((x - delta_x, y + delta_y))
                if self.is_valid_position(x + delta_x, y - delta_y):
                    adjanced_positions.append((x + delta_x, y - delta_y))
                if self.is_valid_position(x - delta_x, y - delta_y):
                    adjanced_positions.append((x - delta_x, y - delta_y))
        return(adjanced_positions)


    # ----------------------------- Board access ------------------------------

    def clear_board(self):
        # This function removes all information about Board_square occupancy,
        # except for flags and stone dictionaries

        for t in range(self.t_dim):
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    self.board_dynamic[t][x][y].remove_stones()

    def create_stone(self, new_stone_ID, stone_type, progenitor_flag_ID, player_faction):
        if stone_type == "tank":
            return(Tank(new_stone_ID, progenitor_flag_ID, player_faction, self.t_dim))
        elif stone_type == "bombardier":
            return(Bombardier(new_stone_ID, progenitor_flag_ID, player_faction, self.t_dim))
        else:
            self.print_log(f"ERROR: Unrecognizable stone type {stone_type} on setup.", 0)
            quit()

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

    def record_stones_at_time(self, t):
        # Overwrites stones.history
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

    def causally_free_stones_at_time(self, t):
        causally_free_armies = {}
        for faction in self.factions:
            causally_free_armies[faction] = []
            for stone_ID in self.faction_armies[faction]:
                if self.stone_causal_freedom[stone_ID] == t:
                    causally_free_armies[faction].append(stone_ID)
        return(causally_free_armies)

    def causally_free_stones_at_time_by_player(self, t, player):
        causally_free_army = []
        for stone_ID in self.faction_armies[player]:
            if self.stone_causal_freedom[stone_ID] == t:
                causally_free_army.append(stone_ID)

        return(causally_free_army)

    def did_player_finish_turn(self, player, turn_index):
        # If there are causally free stones in the active timeslice for which no flags exist,
        # the player still hasn't finished their turn.

        # TODO: not true! In the final timeslice, we can pass on stones and
        # leave them causally free for the next round, yet our turn ends.
        # paradigm for now: after touching every stone, your turn ends!
        if player in self.flags_by_turn[turn_index].keys():
            return(True)

        # This function assumes that moves were executed prior to asking,
        # and activity maps were applied.
        if player not in self.flags_by_turn[turn_index].keys():
            return(False)

        round_number, active_timeslice = self.round_from_turn(turn_index)
        currently_causally_free_stones = self.causally_free_stones_at_time_by_player(active_timeslice, player)
        does_every_stone_have_a_corresponding_flag = True
        for free_stone_ID in currently_causally_free_stones:
            does_stone_have_a_corresponding_flag = False
            for flag_ID in self.flags_by_turn[turn_index][player]:
                if self.flags[flag_ID].is_active and self.flags[flag_ID].stone_ID == free_stone_ID:
                    does_stone_have_a_corresponding_flag = True
                    break
            if not does_stone_have_a_corresponding_flag:
                does_every_stone_have_a_corresponding_flag = False
                break
        if does_every_stone_have_a_corresponding_flag:
            return(True)
        else:
            return(False) # Uncommanded causally free stones still exist

    def did_everyone_finish_turn(self, turn_index):
        for faction in self.factions:
            #if faction not in dynamic_data_representation[-1].keys():
            if not self.did_player_finish_turn(faction, turn_index):
                return(False) # Some players still need to add their commands to this turn
        return(True)


    # ---------------------------- Flag management ----------------------------

    # ----------------------------- Flag addition
    # Methods which add new Flags always return the Flag ID

    def add_stone_on_setup(self, faction, stone_type, x, y, a0):
        # This function allows Gamemaster to describe the initial state of the board, which is reverted to for every retrace of causal events
        new_flag = Flag(STPos(-1, x, y), 'add_stone', faction, [stone_type, a0])
        self.setup_squares[x][y].add_flag(new_flag.flag_ID, None)
        self.flags[new_flag.flag_ID] = new_flag

        # Add the correct stone
        self.stones[new_flag.stone_ID] = self.create_stone(new_flag.stone_ID, stone_type, new_flag.flag_ID, faction)

        # Trackers
        self.faction_armies[faction].append(new_flag.stone_ID)
        self.setup_stones[new_flag.stone_ID] = new_flag.flag_ID
        self.scenarios_by_round[0].setup_activity_map[new_flag.flag_ID] = True

        return(new_flag.flag_ID)

    def add_flag_spatial_move(self, stone_ID, t, old_x, old_y, new_x, new_y, new_a):
        new_flag = Flag(STPos(t, old_x, old_y), "spatial_move", self.stones[stone_ID].player_faction, [new_x, new_y, new_a], stone_ID)
        self.board_dynamic[t][old_x][old_y].add_flag(new_flag.flag_ID, stone_ID)
        self.flags[new_flag.flag_ID] = new_flag
        return(new_flag.flag_ID)

    def add_flag_attack(self, stone_ID, t, x, y, attack_arguments = []):
        new_flag = Flag(STPos(t, x, y), "attack", self.stones[stone_ID].player_faction, attack_arguments, stone_ID)
        self.board_dynamic[t][x][y].add_flag(new_flag.flag_ID, stone_ID)
        self.flags[new_flag.flag_ID] = new_flag
        return(new_flag.flag_ID)

    def add_flag_timejump(self, stone_ID, old_t, old_x, old_y, new_stone_type, new_t, new_x, new_y, new_a, adopted_stone_ID = -1):

        round_number, active_timeslice = self.round_from_turn(self.current_turn_index)
        # If adopted_stone_ID specified, instead of creating a new TJI, we adopt an existing one.
        if adopted_stone_ID == -1:
            # The TJI is placed inactive, and may be activated during causal consistency resolution
            tji_flag = Flag(STPos(new_t - 1, new_x, new_y), "time_jump_in", self.stones[stone_ID].player_faction, [new_stone_type, new_a])
            tjo_flag = Flag(STPos(old_t, old_x, old_y), "time_jump_out", self.stones[stone_ID].player_faction, [STPos(new_t - 1, new_x, new_y)], stone_ID, effect = tji_flag.flag_ID)
            tji_flag.initial_cause = tjo_flag.flag_ID

            # We place the flags.
            # The time_jump_in flag is actually placed one t lower than specified (-1 is allowed!), so the child can be controlled on the same time-slice it is placed onto.
            self.board_dynamic[old_t][old_x][old_y].add_flag(tjo_flag.flag_ID, stone_ID)
            if new_t - 1 >= 0:
                self.board_dynamic[new_t - 1][new_x][new_y].add_flag(tji_flag.flag_ID, None)
            if new_t == 0:
                # We place the flag into a special time-slice
                self.setup_squares[new_x][new_y].add_flag(tji_flag.flag_ID, None)
            self.flags[tji_flag.flag_ID] = tji_flag
            self.flags[tjo_flag.flag_ID] = tjo_flag

            # effects start inactive
            self.set_flag_activity(tji_flag.flag_ID, False)

            # Trackers
            self.effects_by_round[round_number].append(tji_flag.flag_ID)

            # We add the new stone into the army
            self.stones[tji_flag.stone_ID] = self.create_stone(tji_flag.stone_ID, new_stone_type, tji_flag.flag_ID, self.stones[stone_ID].player_faction)
            self.faction_armies[self.stones[stone_ID].player_faction].append(tji_flag.stone_ID)
            return(Message("flags added", [tji_flag.flag_ID, tjo_flag.flag_ID]))
        else:
            # First, we find the TJI which summons the stone
            for round_n in range(len(self.effects_by_round)):
                for TJI_ID in self.effects_by_round[round_n]:
                    if self.flags[TJI_ID].stone_ID == adopted_stone_ID and self.flags[TJI_ID].flag_type == "time_jump_in":
                        # We now check if it is allowed to link us up
                        if not (self.flags[TJI_ID].pos.t == new_t - 1 and self.flags[TJI_ID].pos.x == new_x and self.flags[TJI_ID].pos.y == new_y):
                            return(Message("exception", "Specified stone doesn't time-jump-in at the specified square"))
                        if self.stones[stone_ID].player_faction != self.stones[adopted_stone_ID].player_faction:
                            return(Message("exception", "Specified stone belongs to a different faction"))
                        if self.stones[stone_ID].stone_type not in [self.stones[adopted_stone_ID].stone_type, "wildcard"]:
                            return(Message("exception", "Specified stone is of incompatible type"))
                        if self.stones[stone_ID].stone_type not in ["wildcard", self.stones[adopted_stone_ID].stone_type]:
                            return(Message("exception", "Specified stone is of a different type"))
                        if self.flags[TJI_ID].flag_args[1] != new_a:
                            return(Message("exception", "Specified stone jumps in at a different azimuth than proposed"))
                        if round_n == round_number:
                            return(Message("exception", "Specified time-jump-in has been added only this round, and thus hasn't been realised yet."))
                        # This last one is important, since TJIs added this round are always active, but aren't subject to trackers,
                        # and thus their linkage couldn't be resolved!
                        # We can link up!
                        tjo_flag = Flag(STPos(old_t, old_x, old_y), "time_jump_out", self.stones[stone_ID].player_faction, [STPos(new_t - 1, new_x, new_y), TJI_ID], stone_ID, effect = TJI_ID)
                        self.board_dynamic[old_t][old_x][old_y].add_flag(tjo_flag.flag_ID, stone_ID)
                        self.flags[tjo_flag.flag_ID] = tjo_flag
                        return(Message("flags added", [tjo_flag.flag_ID]))

            return(Message("exception", "Specified stone not associated with a time-jump-in"))

    def add_bomb_flag(self, stone_ID, old_t, old_x, old_y, new_t, new_x, new_y):
        round_number, active_timeslice = self.round_from_turn(self.current_turn_index)
        spawn_bomb_flag = Flag(STPos(new_t - 1, new_x, new_y), "spawn_bomb", self.stones[stone_ID].player_faction, [], stone_ID = None)
        attack_flag = Flag(STPos(old_t, old_x, old_y), "attack", self.stones[stone_ID].player_faction, [], stone_ID = stone_ID, effect = spawn_bomb_flag.flag_ID)
        spawn_bomb_flag.initial_cause = attack_flag.flag_ID

        # We place the flags.
        self.board_dynamic[old_t][old_x][old_y].add_flag(attack_flag.flag_ID, stone_ID)
        if new_t - 1 >= 0:
            self.board_dynamic[new_t - 1][new_x][new_y].add_flag(spawn_bomb_flag.flag_ID, None)
        if new_t == 0:
            # We place the flag into a special time-slice
            self.setup_squares[new_x][new_y].add_flag(spawn_bomb_flag.flag_ID, None)
        self.flags[spawn_bomb_flag.flag_ID] = spawn_bomb_flag
        self.flags[attack_flag.flag_ID] = attack_flag

        # effects start inactive
        self.set_flag_activity(spawn_bomb_flag.flag_ID, False)

        # Trackers
        self.effects_by_round[round_number].append(spawn_bomb_flag.flag_ID)

        return(Message("flags added", [spawn_bomb_flag.flag_ID, attack_flag.flag_ID]))

    def add_canonized_flag(self, new_flag, is_setup = False):
        # This is a function used in loading, which can add any flag type, with
        # the assumption that the flag is well-inputted.

        # is_setup is used for stone-adding flags on the zeroth move only,
        # and is useful for the self.setup_stones tracker

        self.flags[new_flag.flag_ID] = new_flag
        if new_flag.flag_type in Flag.stone_generating_flag_types:
            required_actor = None
        else:
            required_actor = new_flag.stone_ID
        if new_flag.pos.t == -1:
            self.setup_squares[new_flag.pos.x][new_flag.pos.y].add_flag(new_flag.flag_ID, required_actor)
        else:
            self.board_dynamic[new_flag.pos.t][new_flag.pos.x][new_flag.pos.y].add_flag(new_flag.flag_ID, required_actor)

        # If this flag creates a stone, that stone is tracked
        if new_flag.flag_type in Flag.stone_generating_flag_types:
            self.stones[new_flag.stone_ID] = self.create_stone(new_flag.stone_ID, new_flag.flag_args[0], new_flag.flag_ID, new_flag.player_faction)
            self.faction_armies[new_flag.player_faction].append(new_flag.stone_ID)
            if is_setup:
                self.setup_stones[new_flag.stone_ID] = new_flag.flag_ID

        return(new_flag.flag_ID)

    def commit_flags(self, flag_ID_list, turn_index, move_author):
        # This updates
        #     -self.flags_by_turn for move execution purposes
        #     -self.new_dynamic_representation for data saving purposes
        # It is a method representing the change of the dynamic state of the game

        # NOTE: move_author is not necessarily equal to the flag.player_faction
        # value - e.g. setup moves are always authored by "GM".
        if len(self.flags_by_turn) <= turn_index:
            print(f"ERROR: Attempted to canonize flags {flag_ID_list} on turn {turn_index}, but the highest available turn index in self.flags_by_turn is {len(self.flags_by_turn) - 1}.")
            return(-1)
        if move_author not in self.flags_by_turn[turn_index]:
            # First batch of flags canonized for this author for this turn.
            self.flags_by_turn[turn_index][move_author] = []
        self.flags_by_turn[turn_index][move_author] += flag_ID_list

        # We fill self.new_dynamic_representation with empty dictionaries until
        # the correct index exists!
        while(len(self.new_dynamic_representation) <= turn_index):
            self.new_dynamic_representation.append({})
        if move_author not in self.new_dynamic_representation[turn_index]:
            # First batch of flags canonized for this author for this turn.
            self.new_dynamic_representation[turn_index][move_author] = self.encode_move_representation(flag_ID_list)
        else:
            self.new_dynamic_representation[turn_index][move_author] += (constants.Gamemaster_delim) + self.encode_move_representation(flag_ID_list)

        # We also record everything into self.dynamic_representation, for full
        # copy and legacy purposes
        while(len(self.dynamic_representation) <= turn_index):
            self.dynamic_representation.append({})
        if move_author not in self.dynamic_representation[turn_index]:
            # First batch of flags canonized for this author for this turn.
            self.dynamic_representation[turn_index][move_author] = self.encode_move_representation(flag_ID_list)
        else:
            self.dynamic_representation[turn_index][move_author] += (constants.Gamemaster_delim) + self.encode_move_representation(flag_ID_list)




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
        for round_i in range(len(self.effects_by_round)):
            if flag_ID in self.effects_by_round[round_i]:
                self.effects_by_round[round_i].remove(flag_ID)

    # ----------------------------- Flag activity

    def set_flag_activity(self, flag_ID, new_is_active):
        self.flags[flag_ID].is_active = new_is_active

    def realise_scenario(self, scenario):
        # activity map = {"setup_AM" : {flag_ID : is active?...}, "effect_AM" : {flag_ID : is active?...}}
        for setup_flag_ID, is_active_val in scenario.setup_activity_map.items():
            self.set_flag_activity(setup_flag_ID, is_active_val)
        for effect_flag_ID, is_active_val in scenario.effect_activity_map.items():
            self.set_flag_activity(effect_flag_ID, is_active_val)


    # -------------------------- Board canonization ---------------------------
    # Board canonization methods take a Board state and assure its validity,
    # either by stone manipulation or flag activity manipulation.

    # ---------------------- Spatial conflict resolution

    def resolve_conflicts(self, t):
        # Resolves conflicts in a specified time-slice
        # Assumes all previous time-slices are canonical (void of conflicts)
        # The paradigm here is as follows: 1 Sokoban; 2 Impasse; 3 Destruction

        # NOTE that this method is completely flag-independent, only dealing
        # with the placement of Stones on board!

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

    # --------------------- Temporal conflict resolution

    def resolve_causal_consistency(self, for_which_round = None):
        # The wrapper for causal consistency methods
        # for_which_round: This method returns a Scenario instance

        # Returns a dict = {"setup_AM" : {setup activity map}, "effect_AM" : {effect activity map}}
        result_activity_map = {"setup_AM" : {}, "effect_AM" : {}}
        result_causality_trackers = {
                "effect_cause_map" : {},
                "stone_inheritance" : {}
            }
        result_scenario = Scenario({}, {}, {}, {})

        if for_which_round is None:
            # Default: for the next round
            current_round, _ = self.round_from_turn(self.current_turn_index)
            for_which_round = current_round + 1

        if for_which_round == 0:
            # Return the all-setup map
            for setup_flag_ID in self.setup_stones.values():
                result_scenario.setup_activity_map[setup_flag_ID] = True
            return(result_scenario)

        # If we are looking into the past (by passing for_which_round not equal
        # to current round), we just load the correct activity map for setup
        # flags AND effects and use it "blindly".
        # This requires a preparation

        # NOTE: This means once we call this method for round n, we cannot call it for an earlier round later!
        active_setup_stones = []#list(self.setup_stones.keys())
        for setup_stone_ID, setup_flag_ID in self.setup_stones.items():
            if self.flags[setup_flag_ID].is_active:
                active_setup_stones.append(setup_stone_ID)
            else:
                result_scenario.setup_activity_map[setup_flag_ID] = False
        # NOTE populating this list depends on the Ruleset

        # Order setup stones by a deterministic criterion from least prioritised to most prioritised

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
                    #self.flags[self.setup_stones[ordered_setup_stones[i]]].is_active = not activity_map[i]
                    self.set_flag_activity(self.setup_stones[ordered_setup_stones[i]], not activity_map[i])

                # We find all causally consistent scenarios for this activity map
                # For round x, we ignore flags added in round x - 1, and thus max_included_round = x - 2
                causally_consistent_scenario = self.find_causally_consistent_scenarios(max_included_round = for_which_round - 2)
                if causally_consistent_scenario is None:
                    continue # Paradox
                else:
                    # We commit to the canonical scenario
                    effect_activity_map, causality_trackers = causally_consistent_scenario
                    result_scenario.effect_activity_map = effect_activity_map
                    result_scenario.effect_cause_map = causality_trackers["effect_cause_map"]
                    result_scenario.stone_inheritance = causality_trackers["stone_inheritance"]

                    # We add all the causes added in the last round, with their causes being the initial causes
                    for effect_ID in self.effects_by_round[for_which_round - 1]:
                        result_scenario.effect_activity_map[effect_ID] = True
                        result_scenario.effect_cause_map[effect_ID] = self.flags[effect_ID].initial_cause
                        if self.flags[self.flags[effect_ID].initial_cause].flag_type == "time_jump_out":
                            result_scenario.stone_inheritance[self.flags[self.flags[effect_ID].initial_cause].stone_ID] = self.flags[effect_ID].stone_ID

                    for i in range(len(activity_map)):
                        if activity_map[i]:
                            self.removed_setup_stones[ordered_setup_stones[i]] = self.setup_stones[ordered_setup_stones[i]]
                        result_scenario.setup_activity_map[self.setup_stones[ordered_setup_stones[i]]] = not activity_map[i]

                    return(result_scenario)

        # If we get to this point, something has gone terribly wrong, as not even
        # the removal of all stones yielded a causally consistent scenario

        # This should theoretically never occur, as deactivating all add_stone flags
        # AND all TJIs should result in a completely empty board, which is always causally consistent.
        return(Message("exception", "Unable to find a causally consistent scenario."))

    def find_causally_consistent_scenarios(self, max_included_round = None):
        # takes the internal causality surjection and returns the top priority
        # activity map {effect ID : is active?} which is causally consistent.
        # Returns None if pdx, (effect activity map, trackers) otherwise

        # A causally consistent scenario is one such that
        #   -For every in-active effect, no stone reaches any corresponding cause
        #   -For every active effect, exactly one stone reaches a corresponding cause

        reference_effect_ID_list = []
        if max_included_round is None:
            # Default: all but the last round
            current_round, _ = self.round_from_turn(self.current_turn_index)
            max_included_round = current_round - 1

        empty_causality_trackers = {
                    "effect_load" : {},
                    "effect_cause_map" : {},
                    "stone_inheritance" : {}
                }
        if max_included_round < 0:
            # No included rounds means trivial activity map
            return({}, empty_causality_trackers)

        """for t_i in range(1, self.t_dim * (for_which_round - 1) + 1):
            for move_flag_IDs in self.flags_by_turn[t_i].values():
                for move_flag_ID in move_flag_IDs:
                    if self.flags[move_flag_ID].flag_type == "time_jump_in":
                        reference_TJI_ID_list.append(move_flag_ID)"""
        for round_number in range(max_included_round + 1):
            reference_effect_ID_list += self.effects_by_round[round_number]


        # We now do an ordering according to the Ruleset. First element = lowest priority.
        ordered_effect_flags = reference_effect_ID_list

        number_of_effects = len(ordered_effect_flags)
        if number_of_effects == 0:
            return({}, empty_causality_trackers) # The only possible scenario is also, by design, causally consistent

        activity_map = [True] * number_of_effects

        # TODO: make the ordering algorithm depend on Ruleset :)

        for n in range(int(np.power(2, number_of_effects))):
            # first, prepare the moves
            how_many_causes_required = {}
            for i in range(number_of_effects):
                # We set the is_active argument according to the activity map
                self.set_flag_activity(ordered_effect_flags[i], activity_map[i])
                if activity_map[i] == True:
                    how_many_causes_required[ordered_effect_flags[i]] = 1
                if activity_map[i] == False:
                    how_many_causes_required[ordered_effect_flags[i]] = 0
            # execute them
            # include the buffer round, but ignore the buffer effects
            current_causality_trackers = self.execute_moves(read_causality_trackers = True, max_turn_index = self.t_dim * (max_included_round + 2), ignore_buffer_effects = True)
            # Now we just compare self.effect_load to how_many_causes_required
            is_scenario_causally_consistent = True
            for effect_ID in ordered_effect_flags:
                if how_many_causes_required[effect_ID] != current_causality_trackers["effect_load"][effect_ID]:
                    is_scenario_causally_consistent = False
                    break
            if is_scenario_causally_consistent:
                causally_consistent_scenario = {}
                for i in range(number_of_effects):
                    causally_consistent_scenario[ordered_effect_flags[i]] = activity_map[i]
                return(causally_consistent_scenario, current_causality_trackers)

            # find the next activity map
            for i in range(number_of_effects):
                if activity_map[i] == True:
                    activity_map[i] = False
                    break
                else:
                    activity_map[i] = True
        # A paradox has been reached
        return(None)

    # ---------------------------- Flag execution -----------------------------
    # This function cleans the board and realises its evolution across t_dim
    # with a fixed flag activity map (given by the object-stored flag args) so
    # that every time-slice is canonical (i.e. free of spatial conflicts).
    # It also tracks timejump bearings and bijections, so that after realising
    # the board, we can check if it is also causally consistent.

    def add_stone_action(self, t, stone_ID, flag_ID):
        if stone_ID not in self.stone_actions[t].keys():
            self.stone_actions[t][stone_ID] = []
        self.stone_actions[t][stone_ID].append(flag_ID)

    def resolve_stone_actions(self, t):
        # Reads tracker and asks Stones to perform actions
        # Note: these actions ALWAYS have to be initiated AFTER their cause.
        for stone_ID in self.stone_actions[t].keys():
            for action_flag_ID in self.stone_actions[t][stone_ID]:
                if self.flags[action_flag_ID].flag_type == "attack":
                    stone_action_msg = self.stones[stone_ID].attack(self, t, self.flags[action_flag_ID].flag_args)
                    if stone_action_msg.header in self.available_board_actions:
                        self.board_actions[stone_action_msg.msg.t][stone_action_msg.msg.x][stone_action_msg.msg.y][stone_action_msg.header] = True




    def execute_moves(self, read_causality_trackers = False, max_turn_index = None, ignore_buffer_effects = False):
        # This function populates Board_squares with stones according to flags
        # placed on up to (and including) turn with i = max_turn_index.

        # Returns a dictionary {
        #     "effect_load" : measured effect load
        #     "effect_cause_map" : the effect->cause map as recorded by activated causes
        #     "stone_inheritance" : measured stone inheritance
        # }
        # or empty dict if read_causality_trackers == False

        # read_causality_trackers: If False, runs faster but returns empty dict
        # max_turn_index: index of last turn whose flags are to be included
        # ignore_buffer_effects: If True, ignores effects placed in the last
        # included round (used when finding scenario).

        if max_turn_index is None:
            max_turn_index = self.current_turn_index #len(self.flags_by_turn) - 1
        max_round_number, max_timeslice = self.round_from_turn(max_turn_index)

        # First, we clear the board
        self.clear_board()
        result_causality_trackers = {}
        if read_causality_trackers:
            result_causality_trackers = {
                    "effect_load" : {},
                    "effect_cause_map" : {},
                    "stone_inheritance" : {}
                }
            for round_n in range(max_round_number): # All but the last round
                for effect_ID in self.effects_by_round[round_n]:
                    result_causality_trackers["effect_load"][effect_ID] = 0

        # Since causal freedom of a stone depends on its trajectory, it is
        # determined in this method and stored in the following dictionary.
        self.stone_causal_freedom = {}
        undetermined_stones = [] # list of stones not determined as c.f.

        # If a stone gets interfered out of its old trajectory and a new
        # trajectory is set for it, it won't slip into the old one in later
        # timeslices. Hence the GOLDEN RULE is as follows:
        #   1. A stone on a square follows the earliest of the applicable flags
        #   2. If a stone follows a flag, it cannot follow an earlier flag in
        #      later timeslices.
        # We could to this by rounds but using sequential flag IDs works, too.
        # Local tracker for this:
        stone_latest_flag_ID = {} # [stone_ID] = flag_ID of latest flag
        # Reset these trackers
        for stone_ID in self.stones.keys():
            self.stone_causal_freedom[stone_ID] = None
            undetermined_stones.append(stone_ID)
            stone_latest_flag_ID[stone_ID] = -1

        # Stone actions
        # We reset the stone actions tracker
        self.stone_actions = repeated_list(self.t_dim, {})
        # We reset the board actions tracker
        for t in range(self.t_dim):
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    self.board_actions[t][x][y] = {}
                    for available_board_action in self.available_board_actions:
                        self.board_actions[t][x][y][available_board_action] = False


        # Then we prepare a flat list of all flag IDs to execute
        flags_to_execute = []
        for t_i in range(max_turn_index + 1):
            for move_flag_IDs in self.flags_by_turn[t_i].values():
                for move_flag_ID in move_flag_IDs:
                    if not ignore_buffer_effects or move_flag_ID not in self.effects_by_round[max_round_number]: # We ignore buffered effects
                        flags_to_execute.append(move_flag_ID)

        # Then, we execute setup flags, i.e. initial stone creation
        for x in range(self.x_dim):
            for y in range(self.y_dim):
                # For setup squares, they are all empty, and so only FLags with
                # no required actor are executed
                for cur_flag_ID in self.setup_squares[x][y].flags[None]:
                    cur_flag = self.flags[cur_flag_ID]
                    if cur_flag_ID in flags_to_execute and cur_flag.is_active:

                        # TODO for progenitor flags, placing a "Bomb" type stone
                        # instead adds 'explosion' to self.board_actions

                        if cur_flag.flag_type == "add_stone":
                            self.place_stone_on_board(STPos(0, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                            self.stone_causal_freedom[cur_flag.stone_ID] = 0
                        if cur_flag.flag_type == "time_jump_in":
                            self.place_stone_on_board(STPos(0, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                            self.stone_causal_freedom[cur_flag.stone_ID] = 0
                        if cur_flag.flag_type == "spawn_bomb":
                            self.board_actions[0][x][y]["explosion"] = True

        # Then, we execute flags for each time slice sequentially
        for t in range(self.t_dim):
            # At t, we are treating the state of the board at t as canonical, and we use it to
            # calculate the state of the board at t + 1. We do this by first naively resolving
            # the flags at t and then executing a conflict resolution routine which reverts
            # moves which result in conflict.


            # Conflict resolution
            self.resolve_conflicts(t)

            # We preliminarily record stone positions for the actions to be resolvable
            self.record_stones_at_time(t)

            # Stone actions resolution
            self.resolve_stone_actions(t)
            # Board actions resolution
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    if self.board_actions[t][x][y]["destruction"]:
                        self.board_dynamic[t][x][y].remove_stones()
                    if self.board_actions[t][x][y]["explosion"]:
                        affected_positions = self.get_adjanced_positions(x, y, number_of_steps = 1)
                        for affected_position in affected_positions:
                            aff_x, aff_y = affected_position
                            self.board_dynamic[t][aff_x][aff_y].remove_stones()
                    if self.board_actions[t][x][y]["tagscreen"]:
                        print(f"A tagscreen was deployed at ({t},{x},{y})!")


            # At this moment, the time-slice t is in its canonical state, and stone history may be recorded
            self.record_stones_at_time(t)

            # As stones may have been removed from the board, we reset all the
            # stones which haven't been committed.
            for stone_ID in undetermined_stones:
                self.stone_causal_freedom[stone_ID] = None

            # Naive flag execution
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    # We execute the Flags with no required actor, and then the
                    # earliest Flag for each Stone present (should only be one)
                    local_flags_to_execute = []
                    for cur_flag_ID in self.board_dynamic[t][x][y].flags[None]:
                        if cur_flag_ID in flags_to_execute and self.flags[cur_flag_ID].is_active:
                            local_flags_to_execute.append(cur_flag_ID)
                    for stone_ID in self.board_dynamic[t][x][y].stones:
                        # Stone exists on board, so we preliminarily set
                        # its causal freedom to here.
                        self.stone_causal_freedom[stone_ID] = t

                        # We assume that the list of flags is already ordered
                        # from earliest to latest
                        if stone_ID in self.board_dynamic[t][x][y].flags.keys():
                            for cur_flag_ID in self.board_dynamic[t][x][y].flags[stone_ID]:
                                if cur_flag_ID in flags_to_execute and self.flags[cur_flag_ID].is_active and stone_latest_flag_ID[stone_ID] < cur_flag_ID:
                                    stone_latest_flag_ID[stone_ID] = cur_flag_ID
                                    local_flags_to_execute.append(cur_flag_ID)
                                    break # only one Flag per stone


                    for cur_flag_ID in local_flags_to_execute:
                        # These flags propagate the stone into the next time-slice, and as such are forbidden at t = self.t_dim - 1
                        # If a stone is propagated onto an occupied square, the square is added to self.conflicting_squares
                        cur_flag = self.flags[cur_flag_ID]
                        if t < self.t_dim - 1:
                            if cur_flag.flag_type == "add_stone":
                                self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                                self.stone_causal_freedom[cur_flag.stone_ID] = t+1
                            if cur_flag.flag_type == "time_jump_in":
                                self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                                self.stone_causal_freedom[cur_flag.stone_ID] = t+1
                            # For the following flags, the stone has to be present in the current time-slice
                            if cur_flag.flag_type == "spatial_move":
                                self.place_stone_on_board(STPos(t+1, cur_flag.flag_args[0], cur_flag.flag_args[1]), cur_flag.stone_ID, [cur_flag.flag_args[2]])
                                self.stone_causal_freedom[cur_flag.stone_ID] = t+1
                            if cur_flag.flag_type == "attack":
                                self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, self.board_dynamic[t][x][y].stone_properties[cur_flag.stone_ID])
                                self.stone_causal_freedom[cur_flag.stone_ID] = t+1
                                self.add_stone_action(t+1, cur_flag.stone_ID, cur_flag.flag_ID)
                            if cur_flag.flag_type == "spawn_bomb":
                                self.board_actions[t+1][x][y]["explosion"] = True
                        # The following flags remove the stone from the board, and as such are the only flags which can be placed at t = t_dim - 1
                        if cur_flag.flag_type == "time_jump_out":
                            # Newly added TJOs which link previous TJIs should be subject to tracker,
                            # but not TJOs added together with new TJIs
                            self.stone_causal_freedom[cur_flag.stone_ID] = None

                        # If the flag effects a previous flag, we read it here. These can be any flags!
                        if read_causality_trackers and cur_flag.effect is not None:
                            if cur_flag.effect in result_causality_trackers["effect_load"].keys():
                                result_causality_trackers["effect_load"][cur_flag.effect] += 1
                                result_causality_trackers["effect_cause_map"][cur_flag.effect] = cur_flag.flag_ID
                                if cur_flag.flag_type == "time_jump_out":
                                    result_causality_trackers["stone_inheritance"][cur_flag.stone_ID] = self.flags[cur_flag.effect].stone_ID
                            # If not in the keys, this has to point at an effect placed in the last round, therefore always active

                    # Stones whose causal freedom is still t are determined with finality
                    for i in range(len(undetermined_stones) - 1, -1, -1):
                        if self.stone_causal_freedom[undetermined_stones[i]] == t:
                            undetermined_stones.pop(i)

        return(result_causality_trackers)


    # -------------------------------------------------------------------------
    # --------------------------- Game loop methods ---------------------------
    # -------------------------------------------------------------------------

    def round_from_turn(self, turn_index):
        # turn_index == 0 -> setup
        # turn_index == 1, 2... t_dim -> round 0
        #            == t_dim + 1, ... 2.t_dim -> round 1 etc
        if turn_index == 0:
            return((0, -1))
        current_round_number = int(np.floor((turn_index - 1) / self.t_dim))
        current_timeslice    = (turn_index - 1) % self.t_dim
        return(current_round_number, current_timeslice)

    def bring_board_to_turn(self, turn_index):

        # NOTE: The state of the board at turn index N (round M, timeslice t)
        # depends on the flags placed on turns 0, 1... N - 1, but the activity
        # map is given by M anyway. That's why we pass turn_index - 1.

        round_number, active_timeslice = self.round_from_turn(turn_index)
        self.print_log(f"Reverting board state to that right before turn {turn_index} (round {round_number}, t {active_timeslice})...", 0)
        if len(self.scenarios_by_round) <= round_number:
            self.print_log(f"Canonizing activity maps recorded only up to round {len(self.scenarios_by_round) - 1}; a temporary activity map will be initialized.", 1)
            quit()
            #current_activity_map = self.resolve_causal_consistency(max_turn_index = turn_index - 1)
        else:
            current_scenario = self.scenarios_by_round[round_number]
        self.realise_scenario(current_scenario)
        self.execute_moves(read_causality_trackers = False, max_turn_index = turn_index - 1, ignore_buffer_effects = False)



    def prompt_player_input(self, cur_time, player):
        # Wrapper for player input

        # TODO: Journal for printing! At a specific debug level the log is identical to TUI
        # TODO: Flag buffer: flags are collected into a list separately from self.flags and
        #       are only committed after input ends (this should make UNDOing safer)

        # TODO: Commits the newly added flags into dynamic representations and returns it
        currently_causally_free_stones = self.causally_free_stones_at_time_by_player(cur_time, player)
        self.print_heading_message(f"Player {player}, it is your turn to command your stones now.", 2)
        if len(currently_causally_free_stones) == 0:
            self.print_heading_message("No causally free stones to command.", 3)
            return(Message("pass"))
        stone_index = 0
        flags_added_this_turn = repeated_list(len(currently_causally_free_stones), None)
        while(stone_index < len(currently_causally_free_stones)):
            cur_stone = currently_causally_free_stones[stone_index]
            cur_pos = self.stones[cur_stone].history[cur_time]
            x, y, a = cur_pos
            self.print_heading_message(f"Command your stone at ({x},{y}).", 3)
            if cur_time < self.t_dim - 1:
                move_msg = self.stones[cur_stone].parse_move_cmd(self, cur_time)
            else:
                move_msg = self.stones[cur_stone].parse_final_move_cmd(self, cur_time)

            if move_msg.header == "option":
                # The user is interacting with gamemaster options
                if move_msg.msg == "quit":
                    #return(-1)
                    #quit()
                    return(Message("option", "quit"))
                if move_msg.msg == "undo":
                    # We revert back to the previous stone
                    stone_index = max(stone_index-1, 0)
                    # We delete the Flag we added to this stone if any
                    if flags_added_this_turn[stone_index] != None:
                        #prev_x, prev_y, prev_a = self.stones[currently_causally_free_stones[player][stone_index]].history[cur_time]
                        for added_flag_ID in flags_added_this_turn[stone_index]:
                            self.remove_flag_from_game(added_flag_ID)
                        flags_added_this_turn[stone_index] = None
                    continue

            if move_msg.header == "flags added":
                # A new Flag was added
                flags_added_this_turn[stone_index] = move_msg.msg

            stone_index += 1

        # Now we flatten the buffer
        # TODO execute flag addition as you flatten
        flat_flags_added_this_turn = []
        for stone_index in range(len(currently_causally_free_stones)):
            if flags_added_this_turn[stone_index] is None:
                continue
            for flag_index in range(len(flags_added_this_turn[stone_index])):
                flat_flags_added_this_turn.append(flags_added_this_turn[stone_index][flag_index])
        #added_dynamic_representation = self.encode_move_representation(flat_flags_added_this_turn)
        #print(added_dynamic_representation) # TODO this should be returned instead
        return(Message("flags added", flat_flags_added_this_turn))

    def standard_game_loop(self):

        # NOTE: These counters are accessed by Flag-adding methods, and thus
        # have to be set to the correct value before any Flag addition occurs!
        self.round_number = 0
        self.current_time = 0

        self.current_turn_index = 0

        while(True):
            self.print_heading_message(f"Round {self.round_number} commences", 0)

            # Realise scenario
            self.realise_scenario(self.scenarios_by_round[self.round_number])

            for self.current_time in range(self.t_dim):
                self.current_turn_index += 1
                self.flags_by_turn.append({}) # NOTE  nahh
                # First, we find the canonical state of the board
                self.execute_moves()

                # Second, we display the board state
                self.print_heading_message(f"Time = {self.current_time}", 1)
                self.print_board_horizontally(active_turn = self.current_turn_index, highlight_active_timeslice = True)

                # Third, for every causally free stone, we ask its owner to place a flag
                for player in self.factions:
                    output_message = self.prompt_player_input(self.current_time, player)
                    #flags_added_by_player = self.prompt_player_input(self.current_time, player)
                    if output_message.header == "flags added":
                        self.commit_flags(output_message.msg, self.current_turn_index, player)
                    elif output_message.header == "pass":
                        # We need to commit an empty datapoint, otherwise game status will think the player still needs to make his turn
                        self.commit_flags([], self.current_turn_index, player)
                    elif output_message.header == "option":
                        if output_message.msg == "quit":
                            return(0)



            # ---------------------- Sorting out time travel --------------------------

            # We have now spanned the entire temporal length of the board, and must now select a causally consistent scenario
            self.print_heading_message("Selecting a causally-consistent scenario", 1)
            scenario_for_next_round = self.resolve_causal_consistency(for_which_round = self.round_number + 1)

            # Commit to the activity map
            if len(self.scenarios_by_round) != self.round_number + 1:
                self.print_log(f"ERROR: self.scenarios_by_round has wrong length ({len(self.scenarios_by_round)}, expected {self.round_number + 1})")
            self.scenarios_by_round.append(scenario_for_next_round)

            self.round_number += 1
            self.effects_by_round.append([])

    def open_game(self, player):
        # This is the method to be called by client!

        self.bring_board_to_turn(self.current_turn_index)
        current_round, active_timeslice = self.round_from_turn(self.current_turn_index)
        self.print_heading_message(f"Resumed: round {current_round}, active timeslice {active_timeslice}", 0)
        self.print_board_horizontally(active_turn = self.current_turn_index, highlight_active_timeslice = True)

        if self.did_player_finish_turn(player, self.current_turn_index):
            # This player has already submitted his moves
            self.print_heading_message(f"Player {player} has already finished his turn, and is waiting for his opponent.", 2)
            # In case key does not exist, we go ahead and populate with empty string
            self.commit_flags([], self.current_turn_index, player)
        else:
            output_message = self.prompt_player_input(active_timeslice, player)
            #flags_added_by_player = self.prompt_player_input(self.current_time, player)
            if output_message.header == "flags added":
                self.commit_flags(output_message.msg, self.current_turn_index, player)
            elif output_message.header == "pass":
                # We need to commit an empty datapoint, otherwise game status will think the player still needs to make his turn
                self.commit_flags([], self.current_turn_index, player)
            elif output_message.header == "option":
                if output_message.msg == "quit":
                    return(0)

        # For every player that didn't play their turn yet, but has no causally
        # free stones, an empty command is added
        for faction in self.factions:
            if not self.did_player_finish_turn(faction, self.current_turn_index):
                currently_causally_free_stones = self.causally_free_stones_at_time_by_player(active_timeslice, faction)
                if len(currently_causally_free_stones) == 0:
                    self.commit_flags([], self.current_turn_index, faction)


        if self.did_everyone_finish_turn(self.current_turn_index):
            # Turn ended
            next_round, next_timeslice = self.round_from_turn(self.current_turn_index + 1)
            if next_round > current_round:
                # Change of round! Canonization routine!
                self.print_heading_message("Selecting a causally-consistent scenario", 1)
                scenario_for_next_round = self.resolve_causal_consistency(for_which_round = next_round)

                # Commit to the activity map
                if len(self.scenarios_by_round) != current_round + 1:
                    self.print_log(f"ERROR: self.scenarios_by_round has wrong length ({len(self.scenarios_by_round)}, expected {current_round + 1})")
                self.scenarios_by_round.append(scenario_for_next_round)

                self.effects_by_round.append([])


            self.flags_by_turn.append({})
            self.current_turn_index += 1
            self.open_game(player)



    # -------------------------------------------------------------------------
    # ---------------------- Data saving/loading methods ----------------------
    # -------------------------------------------------------------------------
    # Saving: Sends stored representation data to python-server connector
    # Loading: Initializes Gamemaster instance from representation data

    # NOTE: Because of the way loading works (basically performing the entire
    # game from the beginning), it has to be fully deterministic (which agrees
    # with the core philosophy of "strategy board game"). Important for c.f.!

    # NOTE: Since the board state is fully determined by the board static data
    # and the flag placement, INDEPENDENT on turn-by-turn placement, a list of
    # flags would be sufficient. However, we still key-code moves by move and
    # player IDs so we can realise the evolution of the game.
    # However, this does help us, as realising the game state at a specific
    # move just means we populate all the flags up to that point and execute
    # them once (together with a causally-consistent scenario selector).

    # NOTE: We can't actually show the state of the board after an arbitrary
    # number of moves, since the correct activity maps are not tracked, and
    # would have to be calculated using complicated iterative algorithms.
    # WRONG: We can! We just trim the added flags, and then we always run a
    # spatial AND temporal consistency check. EZ. The game is deterministic in
    # this way: If we have a series of flag additions and then a canonization
    # routine, then sprinkling more canonizations in-between doesn't change the
    # final state. NOT TRUE: Depending on the ruleset

    # -------------------------------- Saving ---------------------------------

    def encode_static_data_representation(self):
        board_representation = ""
        for y in range(self.y_dim):
            for x in range(self.x_dim):
                cur_char = self.board_static[x][y]
                board_representation += cur_char
        return([self.t_dim, self.x_dim, self.y_dim, board_representation])

    def encode_move_representation(self, list_of_flag_IDs):
        # Since the order of flag addition matters, we order the list in an ascending order by the first element of each element
        sorted_list_of_flag_IDs = sorted(list_of_flag_IDs)

        flag_representation_list = []
        for cur_flag_ID in sorted_list_of_flag_IDs:
            flag_representation_list.append(self.flags[cur_flag_ID].get_flag_representation())
        return((constants.Gamemaster_delim).join(flag_representation_list))

    def trim_empty_turns(self, dynamic_data, tail_element = {}):
        # dynamic_data is a list of dictionaries
        # This method trims empty dictionaries off of the list's tail
        # and also performs a deepcopy on the rest.
        tail_index = len(dynamic_data) - 1
        trimmed_dynamic_data = []
        end_of_tail = False
        for i in range(tail_index, -1, -1):
            if not end_of_tail and dynamic_data[i] == tail_element:
                continue
            else:
                end_of_tail = True
                trimmed_dynamic_data.insert(0, dynamic_data[i])
        return(trimmed_dynamic_data)

    def dump_to_database(self):
        # This method dumps all of the data, and as such should not be used
        # when saving just the changes to an existing game's state.
        static_data_representation = self.encode_static_data_representation()
        dynamic_data_representation = []

        for turn_i in range(len(self.flags_by_turn)):
            dynamic_data_representation.append({})
            for move_author, move_flag_IDs in self.flags_by_turn[turn_i].items():
                dynamic_data_representation[turn_i][move_author] = self.encode_move_representation(move_flag_IDs)
        return(static_data_representation, self.trim_empty_turns(dynamic_data_representation))

    def dump_changes(self):
        return(self.trim_empty_turns(self.new_dynamic_representation))



    # -------------------------------- Loading --------------------------------

    def decode_move_representation(self, move_representation):
        # This is a representation of a move of a specific player, i.e. a value
        # in the turn-indexed dict of moves by player. It is a list of flags.
        # The output is a list of realised Flag objects

        if move_representation == "":
            return([]) # E.g. player had no causally free stones

        result = []
        flag_representation_list = move_representation.split(";")
        for flag_representation in flag_representation_list:
            result.append(Flag.from_str(flag_representation))
        return(result)

    # This is a legacy feature
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
        self.new_dynamic_representation = [] # A fresh start
        self.flags_by_turn = [{"GM" : []}]
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
        self.effects_by_round = [[]]
        self.scenarios_by_round = [Scenario({}, {}, {}, {})]

        for faction in self.factions:
            self.faction_armies[faction] = []

        faction_orientations = {'A': 1, 'B' : 3} #TODO load this from the board dynamically

        # Read the board setup
        for y in range(self.y_dim):
            for x in range(self.x_dim):
                cur_char = board_lines[y+1][x]
                if cur_char in constants.stone_type_representations.keys():
                    stone_to_load = constants.stone_type_representations[cur_char]
                    setup_flag_ID = self.add_stone_on_setup(stone_to_load[0], stone_to_load[1], x, y, faction_orientations[stone_to_load[0]])
                    self.flags_by_turn[0]["GM"].append(setup_flag_ID)
                    # NOTE: setup flags are never added to
                    # self.new_dynamic_representation, since they are copied
                    # there automatically for every new game on creation.
                else:
                    self.board_static[x][y] = cur_char

        # Setup dynamic board squares and board actions
        self.print_log("Setting up dynamic board representation...", 1)
        self.board_dynamic = []
        self.board_actions = []
        for t in range(self.t_dim):
            self.board_dynamic.append([])
            self.board_actions.append([])
            for x in range(self.x_dim):
                self.board_dynamic[t].append([])
                self.board_actions[t].append([])
                for y in range(self.y_dim):
                    self.board_dynamic[t][x].append(Board_square(STPos(t, x, y)))
                    self.board_actions[t][x].append({})

        self.conflicting_squares = repeated_list(self.t_dim, [])

        # Calculate TUI parameters for printing
        self.single_board_width = self.x_dim * 2 + len(str(self.y_dim - 1))
        self.header_width = self.single_board_width * self.t_dim + len(self.board_delim) * (self.t_dim - 1)

        # First turn next
        self.current_turn_index = 1
        self.flags_by_turn.append({})

    def load_board_representation(self, t_dim, x_dim, y_dim, board_representation):
        # Initializes everything from dimensions and a board representation string
        self.print_log(f"Initializing board from static string representation...", 0)

        self.t_dim = t_dim
        self.x_dim = x_dim
        self.y_dim = y_dim

        # initialize the board matrix, indexed as M[x][y]
        self.board_static = []
        for i in range(self.x_dim):
            self.board_static.append([' ']*self.y_dim)

        self.setup_squares = []
        for x in range(self.x_dim):
            self.setup_squares.append([])
            for y in range(self.y_dim):
                self.setup_squares[x].append(Board_square(STPos(-1, x, y)))

        # Setup players
        self.stones = {}
        self.faction_armies = {}
        self.setup_stones = {}
        self.removed_setup_stones = {}
        for faction in self.factions:
            self.faction_armies[faction] = []

        # Load board static
        # board_representation is a string of length x_dim * y_dim, reading the board
        # left-to-right, up-to-down
        for y in range(self.y_dim):
            for x in range(self.x_dim):
                cur_char = board_representation[y * self.x_dim + x]
                self.board_static[x][y] = cur_char
                # TODO here, we also load bases :))

        # Setup dynamic board squares and board actions
        self.print_log("Setting up dynamic board representation...", 1)
        self.board_dynamic = []
        self.board_actions = []
        for t in range(self.t_dim):
            self.board_dynamic.append([])
            self.board_actions.append([])
            for x in range(self.x_dim):
                self.board_dynamic[t].append([])
                self.board_actions[t].append([])
                for y in range(self.y_dim):
                    self.board_dynamic[t][x].append(Board_square(STPos(t, x, y)))
                    self.board_actions[t][x].append({})

        self.conflicting_squares = repeated_list(self.t_dim, [])

        # Calculate TUI parameters for printing
        self.single_board_width = self.x_dim * 2 + len(str(self.y_dim - 1))
        self.header_width = self.single_board_width * self.t_dim + len(self.board_delim) * (self.t_dim - 1)

        # Unlike the legacy method "load_board", this ignored setup moves

    def load_flags_from_representation(self, dynamic_data_representation):
        # This overwrites ALL the flags.
        # We do not commit these into self.new_dynamic_representation, as they
        # represent the old state of the board.

        # Initialize the board initializing flags
        self.flags = {}
        self.flags_by_turn = []

        # round number = number of causally-consistent-scenario selections
        # executed so far (i.e. the number of canonized rounds).
        self.effects_by_round = []

        for turn_id in range(len(dynamic_data_representation)):
            #historic_round_number = dynamic_data_representation[turn_id]["round_number"]#int(np.floor((turn_id - 1) / self.t_dim))
            historic_round_number, historic_timeslice = self.round_from_turn(turn_id)

            self.flags_by_turn.append({})
            for faction in dynamic_data_representation[turn_id].keys():
                move_representation = dynamic_data_representation[turn_id][faction]
                self.flags_by_turn[turn_id][faction] = []
                move_flags = self.decode_move_representation(move_representation)

                effects_added_this_turn = []
                for move_flag in move_flags:
                    self.add_canonized_flag(move_flag, turn_id == 0)
                    self.flags_by_turn[turn_id][faction].append(move_flag.flag_ID)

                    if move_flag.initial_cause is not None:
                        # This is an effect
                        effects_added_this_turn.append(move_flag.flag_ID)
                self.effects_by_round = add_tail_to_list(self.effects_by_round, historic_round_number + 1)
                self.effects_by_round[historic_round_number] += effects_added_this_turn

        # If all of the loaded turns are finished, we prepare the next turn.
        self.current_turn_index = None
        if len(dynamic_data_representation) == 1:
            # only setup occured so far
            self.current_turn_index = 1
        else:
            # We execute all moves except the last one to see if it was finished
            self.execute_moves(max_turn_index = len(dynamic_data_representation) - 2, ignore_buffer_effects = False)


            if self.did_everyone_finish_turn(len(dynamic_data_representation) - 1):
                self.current_turn_index = len(dynamic_data_representation)
            else:
                self.current_turn_index = len(dynamic_data_representation) - 1

        if self.current_turn_index == len(self.flags_by_turn):
            # Prepare new turn
            self.flags_by_turn.append({})

        # We find Scenarios for each started round
        current_round_number, active_timeslice = self.round_from_turn(self.current_turn_index)
        self.effects_by_round = add_tail_to_list(self.effects_by_round, current_round_number + 1, [])

        self.scenarios_by_round = []

        for round_number in range(current_round_number + 1):
            self.print_log(f"Finding for round {round_number}...", 1)
            round_canon_scenario = self.resolve_causal_consistency(for_which_round = round_number)
            self.scenarios_by_round.append(round_canon_scenario)
            self.print_log(f"Effects added this round: {self.effects_by_round[round_number]}...", 2)









    def load_from_database(self, static_data_representation, dynamic_data_representation):
        # This is the big gun. Initializes the Gamemaster instance from a list of rows.
        # static_data_representation is a dictionary with static data.
        # dynamic_data_representation is a list of dictionaries, where the i-th element
        # is a dictionary of moves made in the i-th turn (0 reserved for setup moves).

        self.static_representation = static_data_representation
        self.dynamic_representation = dynamic_data_representation
        self.new_dynamic_representation = []

        try:
            t_dim = int(static_data_representation[0]) #TODO i don't think we need to convert anything here
            x_dim = int(static_data_representation[1])
            y_dim = int(static_data_representation[2])
            board_representation = static_data_representation[3]
        except:
            print(f"load_from_database(static, dynamic) attempted initialization from a badly formatted static data string representation: {static_data_representation}")
            return(-1)

        self.load_board_representation(t_dim, x_dim, y_dim, board_representation)
        self.load_flags_from_representation(dynamic_data_representation)









