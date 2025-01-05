

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

        # players and stones
        self.stones = {} #[ID] = Stone()
        self.faction_armies = {} #[faction] = [ID_1, ID_2 ... ]
        self.factions = ['A', 'B']

        # the board
        self.board_static = [] # [x][y] = type
        self.board_dynamic = [] # [t][x][y] = Board_square

        #self.flag_types = ['add_stone', 'time_jump_out', 'time_jump_in', 'spatial_move', 'attack'] #the order matters in here, actually! spawns first, then moves and shootings
        self.setup_squares = [] # this acts as board_dynamic with t = -1, and only accepts stone creating flags

        self.load_board(board_number)

    def add_stone_on_setup(self, faction, x, y, a0):
        # This function allows Gamemaster to describe the initial state of the board, which is reverted to for every retrace of causal events
        new_flag = Flag('add_stone', faction, [a0])
        new_ID = new_flag.stone_ID
        self.setup_squares[x][y].add_flag(new_flag)
        self.stones[new_ID] = Stone(new_ID, faction)
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
            self.board_static.append(['0']*self.y_dim)

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
                """if cur_char == 'a':
                    self.stones['A'].append(Stone(x, y, 1))
                elif cur_char == 'b':
                    self.stones['B'].append(Stone(x, y, 3))"""
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

    # ----------------- Print functions -------------------------

    def print_heading_message(self, msg, level):
        # smaller the level, bigger the header
        header_size = (self.x_dim * 2 - 1) * self.t_dim + 3 * (self.t_dim - 1)
        if level == 0:
            print('-' * header_size)
            print(st(' ' + msg + ' ', header_size, '-'))
            print('-' * header_size)
        if level == 1:
            print(st(' ' + msg + ' ', header_size, '-'))
        if level == 2:
            print('-' * int(header_size / 4) + ' ' + msg)
        if level >= 3:
            print("# " + msg)

    def print_board_at_time(self, t, print_to_output = True, include_header_line = False):

        def print_stone(board_lines, stone_symbol, stone_position, stone_azimuth):
            if stone_position == -1 or stone_azimuth == -1:
                return(-1)
            stone_x, stone_y = stone_position
            stone_a = stone_azimuth
            cur_x = stone_x * 2
            cur_y = stone_y * 2
            board_lines[cur_y][cur_x] = stone_symbol
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
                    print_stone(board_lines, self.stones[occupant_ID].player_faction, (x, y), self.board_dynamic[t][x][y].stone_properties[occupant_ID][0])

        for i in range(len(board_lines)):
            board_lines[i] = ''.join(board_lines[i])

        if include_header_line:
            header_info = f't = {t}'
            leftover_length = (self.x_dim * 2 - 1) - len(header_info)
            left_padding = int(math.floor(leftover_length / 2))
            right_padding = leftover_length - left_padding
            full_header_str = ' ' * left_padding + header_info + ' ' * right_padding
            board_lines.insert(0, full_header_str)

        board_string = '\n'.join(board_lines)

        if print_to_output:
            print(board_string)
        return(board_lines)

    def print_board_horizontally(self, include_header_line = True):
        board_delim = ' | '
        total_board_lines = self.print_board_at_time(0, print_to_output = False, include_header_line = include_header_line)
        for t in range(1, self.t_dim):
            cur_board_lines = self.print_board_at_time(t, print_to_output = False, include_header_line = include_header_line)
            for i in range(len(cur_board_lines)):
                total_board_lines[i] += board_delim + cur_board_lines[i]
        board_string = '\n'.join(total_board_lines)
        print(board_string)
        print("-" * ((self.x_dim * 2 - 1) * self.t_dim + len(board_delim) * (self.t_dim - 1)))


    # ----------------------------------------------------
    # ----------- board manipulation functions -----------
    # ----------------------------------------------------

    # board access

    def clear_board(self):
        # This function removes all information about Board_square occupancy,
        # except for flags and stone dictionaries

        for t in range(self.t_dim):
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    self.board_dynamic[t][x][y].remove_stone

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
                self.print_heading_message(f"Time = {self.current_time}", 1)
                self.print_board_horizontally()

            break





lol = Gamemaster(1)

lol.execute_moves()
lol.print_board_horizontally()
#print(lol.causally_free_stones_at_time(0))
#print(lol.causally_free_stones_at_time(1))
lol.standard_game_loop()
