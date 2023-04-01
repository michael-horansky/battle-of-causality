

import math
from stone_class import *


class board_move():
    def __init__(self, move_type, player_faction, move_args):
        self.move_type = move_type
        self.player_faction = player_faction
        self.move_args = move_args.copy()
    
    def get_args(self):
        if self.move_type == 'spatial_move':
            # args = [t, pos0, pos1, a1]
            return(self.args[0], self.args[1], self.args[2], self.args[3])
        if self.move_type == 'time_jump':
            # args = [pos, t0, t1]
            return(self.args[0], self.args[1], self.args[2])

class gamemaster():
    
    # ----------------------------------------------------
    # ------ constructors, destructors, descriptors ------
    # ----------------------------------------------------
    
    def __init__(self, board_number):
        
        self.stones = {}
        self.factions = ['A', 'B']
        self.load_board(board_number)
        # move stone config to board file?
        #self.stones['A'] = stones_A
        #self.stones['B'] = stones_B
        
        self.moves = []

    def load_board(self, board_number):
        
        # load spatial and temporal dimensions of the board from the provided txt file
        print("gamemaster.load_board")
        board_file = open("resources/boards/board_" + uniform_str(board_number, 3) + ".txt", 'r')
        board_lines = board_file.readlines()
        board_file.close()
        
        for i in range(len(board_lines)):
            if board_lines[i][-1] == '\n':
                board_lines[i] = board_lines[i][:-1]
        
        self.x_dim = len(board_lines[1])
        self.y_dim = len(board_lines) - 1
        
        # initialize the board matrix, indexed as M[x][y]
        
        self.board = []
        for i in range(self.x_dim):
            self.board.append(['0']*self.y_dim)
        
        self.T = int(board_lines[0])
        #self.stones = {'A' : [], 'B' : []}
        self.stones = {}
        for faction in self.factions:
            self.stones[faction] = []
        
        faction_orientations = {'A': 1, 'B' : 3} #TODO load this from the board dynamically
        
        for y in range(len(board_lines)-1):
            for x in range(len(board_lines[y+1])):
                cur_char = board_lines[y+1][x]
                """if cur_char == 'a':
                    self.stones['A'].append(stone(x, y, 1))
                elif cur_char == 'b':
                    self.stones['B'].append(stone(x, y, 3))"""
                if cur_char.upper() in self.factions:
                    self.stones[cur_char.upper()].append(stone(x, y, faction_orientations[cur_char.upper()]))
                else:
                    self.board[x][y] = cur_char
    
    def get_square(self, pos):
        x, y = pos
        return(self.board[x][y])
    
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
                board_lines[cur_y][cur_x] = '^'
            if stone_a == 1:
                cur_x += 1
                board_lines[cur_y][cur_x] = '>'
            if stone_a == 2:
                cur_y += 1
                board_lines[cur_y][cur_x] = 'v'
            if stone_a == 3:
                cur_x -= 1
                board_lines[cur_y][cur_x] = '<'
        
        # board lines: list of rows
        board_lines = repeated_list(self.y_dim * 2 - 1, repeated_list(self.x_dim * 2 - 1, ' '))
        for i in range(self.x_dim):
            for j in range(self.y_dim):
                board_lines[2 * i][2 * j] = self.board[j][i]
        
        """for stone in self.stones['A']:
            print_stone(board_lines, 'A', stone.get_position(t))
        for stone in self.stones['B']:
            print_stone(board_lines, 'B', stone.get_position(t))
        """ 
        for faction in self.factions:
            for stone in self.stones[faction]:
                print_stone(board_lines, faction, stone.get_position(t), stone.get_azimuth(t))
        
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
        for t in range(1, self.T):
            cur_board_lines = self.print_board_at_time(t, print_to_output = False, include_header_line = include_header_line)
            for i in range(len(cur_board_lines)):
                total_board_lines[i] += board_delim + cur_board_lines[i]
        board_string = '\n'.join(total_board_lines)
        print(board_string)
        print("-" * ((self.x_dim * 2 - 1) * self.T + len(board_delim) * (self.T - 1)))
    
    
    # ----------------------------------------------------
    # ----------- board manipulation functions -----------
    # ----------------------------------------------------
    
    # board access
    
    def reset_board(self):
        for faction in self.factions:
            for faction_stone_i in range(len(self.stones[faction])):
                faction_stone = self.stones[faction][faction_stone_i]
                reset_msg = faction_stone.reset_stone()
                if reset_msg == 'child':
                    del self.stones[faction][faction_stone_i]
    
    def is_board_symbol_available(self, symbol):
        if symbol.upper() in ['X']:
            return(False)
        return(True)
    
    def is_box_pushable(self, t, pos, approach_azimuth):
        # approach_azimuth == -1 means we're time jumping onto this square
        if approach_azimuth == -1:
            return(False)
        new_pos = pos_step(pos, approach_azimuth)
        return(self.is_pos_available(t, new_pos, approach_azimuth, allow_box_pushing = False)) #a box cannot push another box
        
    
    def is_pos_available(self, t, pos, approach_azimuth, player_faction = -1, allow_box_pushing = True):
        if not self.is_board_symbol_available(self.get_square(pos)):
            return(False)
        if self.find_stone_at_position(t, pos, player_faction = player_faction, debug_msg = False) != -1:
            return(False)
        """
        if box at t, pos:
            if allow_box_pushing == False:
                return(False)
            else:
                if not self.is_box_pushable(t, pos, approach_azimuth):
                    return(False)
        """
        return(True)
    
    def find_stone_at_position(self, t, pos, player_faction = -1, debug_msg = True):
        
        if player_faction == -1:
            for faction in self.factions:
                for faction_stone in self.stones[faction]:
                    if faction_stone.get_position(t) == pos:
                        return(faction_stone)
        else:
            for faction_stone in self.stones[player_faction]:
                if faction_stone.get_position(t) == pos:
                    return(faction_stone)
        if debug_msg:
            print(f"No stone found at t = {t}, position = {pos}")
        return(-1)
    
    def change_stone_position(self, t, pos0, pos1, a1 = -1, player_faction = -1):
        # a1 = -1 means we keep the old azimuth
        # player_faction != -1 means we only move the stone if it belongs to a specific faction
        
        # First, check if a stone exists in this position
        cur_stone = self.find_stone_at_position(t, pos0)
        if cur_stone != -1:
            # test if illegal move
            if self.is_pos_available(t, pos1, get_azimuth_from_delta_pos(pos0, pos1), player_faction = player_faction, allow_box_pushing = True):
                cur_stone.position[t] = pos1
                if a1 != -1:
                    cur_stone.azimuth[t] = a1
                return(self)
            else:
                print("Illegal move")
        return(-1)
    
    def move_stone_individually(self, t, pos0, pos1, a1):
        # Takes a stone's last set position and appends the new one
        cur_stone = self.find_stone_at_position(t, pos0)
        if cur_stone != -1:
            if len(cur_stone.position) == t+1:
                # test if illegal move
                if self.is_pos_available(t, pos1, get_azimuth_from_delta_pos(pos0, pos1), allow_box_pushing = True):
                    cur_stone.position.append(pos1)
                    cur_stone.azimuth.append(a1)
                    return(self)
                else:
                    print("Illegal move")
        return(-1)
    
    def copy_board_onto_next_t(self, t):
        for faction in self.factions:
            for stone in self.stones[faction]:
                if stone.get_position(t+1) == -1 and stone.get_position(t) == -1:
                    continue
                if stone.get_position(t+1) == -1 and stone.get_position(t) != -1:
                    stone.position.append(stone.get_position(t))
                    stone.azimuth.append(stone.get_azimuth(t))
                else:
                    stone.position[t+1] = stone.position[t]
                    stone.azimuth[t+1] = stone.azimuth[t]
    
    def move_stone(self, t, pos0, pos1, a1 = -1, player_faction = -1):
        # like a chess move: the board carries over. This obviously overwrites all other stone moves from t to t+1
        # aborts if move illegal
        
        if type(pos0) != list:
            pos0 = [pos0]
            pos1 = [pos1]
            a1 = [a1]
            player_faction = [player_faction]
        
        all_moves_legal = True
        for i in range(len(pos0)):
            if not self.is_pos_available(t, pos1[i], get_azimuth_from_delta_pos(pos0[i], pos1[i]), allow_box_pushing = True):
                all_moves_legal = False
                break
            stone_at_position = self.find_stone_at_position(t, pos0[i], player_faction = player_faction[i], debug_msg = False)
            if stone_at_position == -1:
                # no stone
                all_moves_legal = False
                break
            if stone_at_position.get_position(t+1) != -1:
                # stone is causally linked to the future and cannot be moved
                all_moves_legal = False
                break
        if all_moves_legal == False:
            #print("Some moves are illegal")
            return(-1)
        
        
        self.copy_board_onto_next_t(t)
        for i in range(len(pos0)):
            self.change_stone_position(t+1, pos0[i], pos1[i], a1[i], player_faction[i])
        
    # move history access
    
    def add_spatial_move(self, t, pos0, pos1, a1 = -1, player_faction = -1):
        new_move = board_move('spatial_move', player_faction, [t, pos0, pos1, a1])
        self.moves.append(new_move)
        self.move_stone(t, pos0, pos1, a1, player_faction)
    
    def add_time_jump(self, pos, t0, t1, player_faction = -1):
        new_move = board_move('time_jump', player_faction, [pos, t0, t1])
        self.moves.append(new_move)
        # self.time_jump_stone(pos, t0, t1, player_faction)
    
    def execute_moves(self, exit_on_illegal_move = False):
        # resets the board, executes all the moves in order
        self.reset_board()
        for move in self.moves:
            move_msg = -1
            if move.move_type == 'spatial_move':
                move_msg = self.move_stone(*move.move_args, move.player_faction)
            #if move.move_type == 'time_jump':
            #    move_msg = self.time_jump_stone(*move.move_args, move.player_faction)
            if move_msg == -1 and exit_on_illegal_move == True:
                print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
            
        
