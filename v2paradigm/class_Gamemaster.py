

import math
from functions import *
from class_Stone import Stone
from class_Flag import Flag
from class_Board_square import Board_square

# ---------------------------------------------
# ---------------- class STPos ----------------
# ---------------------------------------------
# A simple structure where every instance encodes a single spacetime position

class STPos():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y

    def __str__(self):
        return(f"{{t:{self.t}, x:{self.x}, y:{self.y}}}")
    def __repr__(self):
        return(self.__str__())

# ---------------------------------------------
# ------------- class Gamemaster --------------
# ---------------------------------------------

class Gamemaster():

    # ----------------------------------------------------
    # ------ constructors, destructors, descriptors ------
    # ----------------------------------------------------

    def __init__(self, board_number):

        # players and stones. The lists are updated when flags are placed, and do not depend on which stones are actually present on the board dynamically.
        self.stones = {} #[ID] = Stone()
        self.faction_armies = {} #[faction] = [ID_1, ID_2 ... ]
        self.factions = ['A', 'B']

        # the board
        self.board_static = [] # [x][y] = type
        self.board_dynamic = [] # [t][x][y] = Board_square
        self.conflicting_squares = [] # [t] = (x,y) of a board square which is occupied by more than one stone at time t

        #self.flag_types = ['add_stone', 'time_jump_out', 'time_jump_in', 'spatial_move', 'attack'] #the order matters in here, actually! spawns first, then moves and shootings
        self.setup_squares = [] # this acts as board_dynamic with t = -1, and only accepts stone creating flags

        # TUI elements
        self.board_delim = ' | '

        self.load_board(board_number)

    def add_stone_on_setup(self, faction, x, y, a0):
        # This function allows Gamemaster to describe the initial state of the board, which is reverted to for every retrace of causal events
        new_flag = Flag('add_stone', faction, [a0])
        new_ID = new_flag.stone_ID
        self.setup_squares[x][y].add_flag(new_flag)
        self.stones[new_ID] = Stone(new_ID, faction, self.t_dim)
        self.faction_armies[faction].append(new_ID)

    def load_board(self, board_number):
        # load spatial and temporal dimensions of the board from the provided txt file
        print("gamemaster.load_board")
        self.round_number = 0
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
        self.setup_squares = []
        for x in range(self.x_dim):
            self.setup_squares.append([])
            for y in range(self.y_dim):
                self.setup_squares[x].append(Board_square(STPos(-1, x, y)))

        self.t_dim = int(board_lines[0])

        # Setup players
        self.stones = {}
        self.faction_armies = {}
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

    def print_board_at_time(self, t, print_to_output = True, include_header_line = False, is_active = False):

        def print_stone(board_lines, stone_symbol, stone_position, stone_azimuth, highlight = False):
            if stone_position == -1 or stone_azimuth == -1:
                return(-1)
            stone_x, stone_y = stone_position
            stone_a = stone_azimuth
            cur_x = stone_x * 2
            cur_y = stone_y * 2

            stone_formatting_pre = ''
            stone_formatting_suf = ''
            if highlight:
                stone_formatting_pre = color.BOLD
                stone_formatting_suf = color.LIGHT

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
                if self.board_dynamic[t][x][y].occupied:
                    occupant_ID = self.board_dynamic[t][x][y].stones[0]
                    is_occupant_causally_free = occupant_ID in self.board_dynamic[t][x][y].causally_free_stones
                    print_stone(board_lines, self.stones[occupant_ID].player_faction, (x, y), self.board_dynamic[t][x][y].stone_properties[occupant_ID][0], highlight = is_occupant_causally_free)

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

    def print_board_horizontally(self, highlight_t = -1):
        # Causally free stones are BOLD
        # if highlight_t selected, the corresponding board is in GREEN
        total_board_lines = self.print_board_at_time(0, print_to_output = False, include_header_line = True, is_active = (highlight_t == 0))
        for t in range(1, self.t_dim):
            cur_board_lines = self.print_board_at_time(t, print_to_output = False, include_header_line = True, is_active = (highlight_t == t))
            for i in range(len(cur_board_lines)):
                total_board_lines[i] += self.board_delim + cur_board_lines[i]
        board_string = '\n'.join(total_board_lines)
        print(board_string)
        print("-" * self.header_width)


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

    def change_stone_pos(self, stone_ID, t, old_x, old_y, new_x, new_y):
        if not stone_ID in self.board_dynamic[t][old_x][old_y].stones:
            print(f"Error: Gamemaster.change_stone_pos attempted to move stone {stone_ID} from ({t},{old_x},{old_y}), where it currently isn't.")
            return(-1)
        self.board_dynamic[t][new_x][new_y].add_stone(stone_ID, self.board_dynamic[t][old_x][old_y].stone_properties[stone_ID])
        self.board_dynamic[t][old_x][old_y].remove_stone(stone_ID)

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
                            self.change_stone_pos(self, stone_a, t, x, y, new_pos_x, new_pos_y)
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
                            self.change_stone_pos(self, stone_b, t, x, y, new_pos_x, new_pos_y)
                            # We remove the conflict
                            self.conflicting_squares[t].remove((x, y))

        # 2 Impasse
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
                for cur_ID in self.board_dynamic[t][x][y].stones:
                    if cur_ID in stones_checked:
                        # The stone has already been moved back
                        continue
                    stones_checked.append(cur_ID)
                    previous_pos = self.stones[cur_ID].history[t-1]
                    if previous_pos == None:
                        # The stone was just added onto the board.
                        continue
                    prev_x, prev_y = previous_pos
                    if prev_x == x and prev_y == y:
                        # The stone was waiting in the previous time-slice, and is not to be moved.
                        continue
                    # We move the stone back. If the previous square is occupied or unavailable, we add it to squares_to_be_checked
                    if self.board_dynamic[t][prev_x][prev_y].occupied or (not self.is_square_available(prev_x, prev_y)):
                        if not previous_pos in squares_to_be_checked:
                            squares_to_be_checked.append(previous_pos)
                        if not previous_pos in self.conflicting_squares[t]:
                            self.conflicting_squares[t].append(previous_pos)
                    self.change_stone_pos(self, cur_ID, t, x, y, prev_x, prev_y)
                # We check if the square is no longer conflicting. If not, we remove it from self.conflicting_squares[t]
                if self.is_square_available(x, y):
                    if len(self.board_dynamic[t][x][y].stones) < 2:
                        self.conflicting_squares[t].remove(cur_pos)
                elif not self.board_dynamic[t][x][y].occupied:
                    self.conflicting_squares[t].remove(cur_pos)

        # 3 Explosion
        # We remove all stones from all remaining conflicting squares
        while(len(self.conflicting_squares[t]) > 0):
            cur_pos = self.conflicting_squares[t].pop(0)
            x, y = cur_pos
            self.board_dynamic[t][x][y].remove_stones()





    def execute_moves(self):
        # This function populates Board_squares with stones according to all flags

        # First, we clear the board
        self.clear_board()

        # Then, we execute setup flags, i.e. initial stone creation
        for x in range(self.x_dim):
            for y in range(self.y_dim):
                for cur_flag in self.setup_squares[x][y].flags:
                    if cur_flag.flag_type == "add_stone":
                        self.board_dynamic[0][x][y].add_stone(cur_flag.stone_ID, cur_flag.flag_args)

        # Then, we execute flags for each time slice sequantially
        # TODO
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
                    for cur_flag in self.board_dynamic[t][x][y].flags:
                        # Flag switch here

                        # These flags propagate the stone into the next time-slice, and as such are forbidden at t = self.t_dim - 1
                        # If a stone is propagated onto an occupied square, the square is added to self.conflicting_squares
                        if t < self.t_dim - 1:
                            if cur_flag.flag_type == "add_stone":
                                self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, [cur_flag.flag_args[0]])
                            if cur_flag.flag_type == "time_jump_in":
                                self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, [cur_flag.flag_args[1]])
                            # For the following flags, the stone has to be present in the current time-slice
                            if cur_flag.stone_ID in self.board_dynamic[t][x][y].stones:
                                if cur_flag.flag_type == "spatial_move":
                                    self.place_stone_on_board(STPos(t+1, cur_flag.flag_args[0], cur_flag.flag_args[1]), cur_flag.stone_ID, [cur_flag.flag_args[2]])
                                if cur_flag.flag_type == "attack":
                                    self.place_stone_on_board(STPos(t+1, x, y), cur_flag.stone_ID, self.board_dynamic[t+1][x][y].stone_properties[cur_flag.stone_ID])
                                    # TODO resolve attack here
                        # The following flags remove the stone from the board, and as such are the only flags which can be placed at t = t_dim - 1
                        if cur_flag.stone_ID in self.board_dynamic[t][x][y].stones:
                            if cur_flag.flag_type == "time_jump_out":
                                continue
                                # TODO Does anything need to happen here? Methinks not; this flag is only relevant for finding self-consistent causal scenarios at the end of each round








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

            break





lol = Gamemaster(1)

#lol.execute_moves()
#print(lol.causally_free_stones_at_time(0))
#print(lol.causally_free_stones_at_time(1))
lol.standard_game_loop()
