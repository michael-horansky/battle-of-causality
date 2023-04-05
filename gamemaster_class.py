

import math
from stone_class import *

def human_readable_azimuth(a):
    if a == 0:
        return('up')
    if a == 1:
        return('right')
    if a == 2:
        return('down')
    if a == 3:
        return('left')
    return('jump')

def get_position_list_for_spawn(t, pos):
    if t == 0:
        return([pos])
    else:
        return([-1] * (t-1) + [pos])

        

class board_move():
    # actually a flag
    """
    flags that are not ANONYMOUS are tied to a specific stone by its ID (which is a static variable that rises incrementally). They don't act on stones with different IDs
        IDs are added as an arg in add_stone and time_jump_out so that they can be invariably associated with a specific stone
    flags that are ANONYMOUS aren't associated with an existing stone, but usually create a stone or cause a different event
    """
    stone_generating_move_types = ['add_stone', 'time_jump_in']
    max_ID = 0
    @staticmethod
    def get_ID_tag():
        new_tag = board_move.max_ID
        board_move.max_ID += 1
        return(new_tag)
    
    def __init__(self, move_type, round_number, player_faction, pos, move_args, stone_ID = -1):
        self.move_type = move_type
        self.player_faction = player_faction
        self.pos = pos
        self.move_args = move_args.copy()
        self.stone_ID = stone_ID #-1 for anonymous flags, a non-negative integer otherwise
        if self.move_type in board_move.stone_generating_move_types:
            self.stone_ID = board_move.get_ID_tag()
        
        # each move progresses causal freedom of all the stones that were around when it was made
        # hence we just have a toggle whether this move was made in the LAST ROUND
        # for more general support, we keep the round in which each move was made
        self.round_number = round_number
    
    def __str__(self):
        str_rep = 'UNDEFINED_MOVE'
        if self.move_type == 'add_stone':
            str_rep = f"Add stone unconditionally (P. '{self.player_faction}', ID {self.stone_ID}): {self.pos} [{human_readable_azimuth(self.move_args[0])}]"
        if self.move_type == 'spatial_move':
            str_rep = f"Spatial move (P. '{self.player_faction}', ID {self.stone_ID}): {self.pos} -> {self.move_args[0]} [{human_readable_azimuth(self.move_args[1])}]"
        return(str_rep)
    
    def __repr__(self):
        return(self.__str__())
    
    def get_args(self):
        if self.move_type == 'add_stone':
            # args = [a]
            return(self.move_args[0])
        if self.move_type == 'time_jump_out':
            # args = [t_target]
            return(self.move_args[0])
        if self.move_type == 'time_jump_in':
            # args = [is_active, new_stone_ID]
            return(self.move_args[0], self.move_args[1])
        if self.move_type == 'spatial_move':
            # args = [pos_target, a_target]
            return(self.move_args[0], self.move_args[1])

class gamemaster():
    
    # ----------------------------------------------------
    # ------ constructors, destructors, descriptors ------
    # ----------------------------------------------------
    
    def __init__(self, board_number):
        
        self.stones = {}
        self.factions = ['A', 'B']
        # move stone config to board file?
        #self.stones['A'] = stones_A
        #self.stones['B'] = stones_B
        
        self.moves = []
        # we abolishing thr MOVES system in favour of the HISTORY system
        self.flag_types = ['add_stone', 'spatial_move'] #the order matters in here, actually! spawns first, then moves and shootings (although those happen simultaneously)
        self.history = []
        # self.history[time] = {'add_stone' : [add_stone1, add_stone2...], 'spatial_move' : [move1, move2...]}
        self.setup_moves = []
        
        self.load_board(board_number)
        
    
    def add_stone_on_setup(self, faction, pos0, a0):
        new_move = board_move('add_stone', 0, faction, pos0, [a0])
        new_ID = new_move.stone_ID
        self.setup_moves.append(new_move)
        self.history[0]['add_stone'].append(new_move)
        self.stones[faction].append(Stone(new_ID, 0, faction, pos0, a0))

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
        
        self.board = []
        for i in range(self.x_dim):
            self.board.append(['0']*self.y_dim)
        
        self.T = int(board_lines[0])
        self.history = []
        for t in range(self.T):
            self.history.append({})
            for flag_type in self.flag_types:
                self.history[t][flag_type] = []
        #self.stones = {'A' : [], 'B' : []}
        self.stones = {}
        for faction in self.factions:
            self.stones[faction] = []
        
        faction_orientations = {'A': 1, 'B' : 3} #TODO load this from the board dynamically
        
        for y in range(len(board_lines)-1):
            for x in range(len(board_lines[y+1])):
                cur_char = board_lines[y+1][x]
                """if cur_char == 'a':
                    self.stones['A'].append(Stone(x, y, 1))
                elif cur_char == 'b':
                    self.stones['B'].append(Stone(x, y, 3))"""
                if cur_char.upper() in self.factions:
                    self.add_stone_on_setup(cur_char.upper(), (x, y), faction_orientations[cur_char.upper()])
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
                del self.stones[faction][0]
        """faction_stone = self.stones[faction][faction_stone_i]
                reset_msg = faction_stone.reset_stone()
                if reset_msg == 'child':
                    del self.stones[faction][faction_stone_i]"""
    
    def is_board_symbol_available(self, symbol):
        if symbol.upper() in ['X']:
            return(False)
        return(True)
    
    def is_box_pushable(self, t, pos, approach_azimuth):
        # approach_azimuth == -1 means we're time jumping onto this square
        if approach_azimuth == -1:
            return(False)
        new_pos = pos_step(pos, approach_azimuth)
        return(self.is_pos_available(t, pos, new_pos, allow_box_pushing = False)) #a box cannot push another box
        
    
    def is_pos_available(self, t, pos0, pos1, player_faction = -1, allow_box_pushing = True):
        approach_azimuth = get_azimuth_from_delta_pos(pos0, pos1)
        if not self.is_board_symbol_available(self.get_square(pos1)):
            return(False)
        if self.find_stone_at_position(t, pos1, player_faction = player_faction, debug_msg = False) != -1:
            return(False)
        """
        if box at t, pos1:
            if allow_box_pushing == False:
                return(False)
            else:
                if not self.is_box_pushable(t, pos1, approach_azimuth):
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
            if self.is_pos_available(t, pos0, pos1, player_faction = player_faction, allow_box_pushing = True):
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
                if self.is_pos_available(t, pos0, pos1, allow_box_pushing = True):
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
            if not (pos0 == pos1[i] or self.is_pos_available(t, pos0, pos1[i], allow_box_pushing = True)):
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
        target_stone = self.find_stone_at_position(t, pos0)
        if target_stone == -1:
            return(-1)
        if not (pos0 == pos1 or self.is_pos_available(t, pos0, pos1, player_faction = player_faction, allow_box_pushing = True)):
            return(-1)
        if player_faction != -1 and target_stone.player_faction != player_faction:
            return(-1)
        if not target_stone.is_causally_free(t):
            print("bugger off")
            return(-1)
        self.history[t]['spatial_move'].append(board_move('spatial_move', self.round_number, target_stone.player_faction, pos0, [pos1, a1], target_stone.ID))
        
        """new_move = board_move('spatial_move', player_faction, [t, pos0, pos1, a1])
        move_msg = self.move_stone(t, pos0, pos1, a1, player_faction)
        if move_msg != -1:
            self.moves.append(new_move)
        return(move_msg)"""
    
    def add_time_jump(self, pos, t0, t1, player_faction = -1):
        new_move = board_move('time_jump', self.round_number, player_faction, [pos, t0, t1])
        self.moves.append(new_move)
        # self.time_jump_stone(pos, t0, t1, player_faction)
    
    def execute_moves(self, max_t = -1, exit_on_illegal_move = False):
        # resets the board, executes all the moves in order: transforms history into stone evolution
        if max_t == -1:
            max_t = self.T
        self.reset_board()
        for t in range(max_t):
            if t > 0:
                self.copy_board_onto_next_t(t - 1)
            # TODO SIMULTANEOUS CONFLICT RESOLUTION!!! (what if two stones want to go to the same spot at the same time? first come first serve is bad)
            
            no_moves = True
            
            for add_stone_move in self.history[t]['add_stone']:
                if self.is_pos_available(t, add_stone_move.pos, add_stone_move.pos, add_stone_move.player_faction, allow_box_pushing = False):
                    pos_0 = get_position_list_for_spawn(t, add_stone_move.pos)
                    a_0   = get_position_list_for_spawn(t, add_stone_move.move_args[0])
                    #print("keheeee", stone)
                    self.stones[add_stone_move.player_faction].append(Stone(add_stone_move.stone_ID, add_stone_move.round_number, add_stone_move.player_faction, pos_0, a_0))
                    
                    no_moves = False
                elif exit_on_illegal_move:
                    print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                    return(-1)
            
            for spatial_move in self.history[t]['spatial_move']:
                target_stone = self.find_stone_at_position(t, spatial_move.pos)
                if target_stone == -1:
                    if exit_on_illegal_move:
                        print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                        return(-1)
                    continue
                if target_stone.ID != spatial_move.stone_ID:
                    if exit_on_illegal_move:
                        print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                        return(-1)
                    continue
                pos1 = spatial_move.move_args[0]
                a1   = spatial_move.move_args[1]
                if not (spatial_move.pos == pos1 or self.is_pos_available(t, spatial_move.pos, pos1, player_faction = spatial_move.player_faction, allow_box_pushing = True)):
                    if exit_on_illegal_move:
                        print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                        return(-1)
                    continue
                else:
                    target_stone.position[t] = pos1
                    if a1 != -1:
                        target_stone.azimuth[t] = a1
                    
                    no_moves = False
            
            for mt in self.flag_types:
                for move in self.history[t][mt]:
                    for faction in self.factions:
                        for stone in self.stones[faction]:
                            stone.progress_causal_freedom(t, self.T, move.round_number)
                #break
        """
        for move in self.moves:
            move_msg = -1
            if move.move_type == 'spatial_move':
                move_msg = self.move_Stone(*move.move_args, move.player_faction)
            #if move.move_type == 'time_jump':
            #    move_msg = self.time_jump_Stone(*move.move_args, move.player_faction)
            if move_msg == -1 and exit_on_illegal_move == True:
                print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                return(-1)"""
    
    
    # ----------------------------------------------------
    # --------------- game loop functions ----------------
    # ----------------------------------------------------
    
    def standard_game_loop(self):
        """
        in this mode, the game ends when one of the following conditions is met:
            a. No players except one have any available stone lines (all their stones end up dead) - the remaining player is the winner
            b. A round that doesn't result in a paradox doesn't happen after N tries (usually set N = 2) - the player with the largest number of
                available stone lines wins
        In each round, there are 3 phases:
            1. all players choose any number of stones at the end of their stone lines that will jump back in time, each of them to any t<T
                (this phase is omitted in the 1st round: instead, all stones are treated as if they travelled to t = 0, with the board history being empty)
            2. In this phase, the clock is reset to t=0, and then the following process loops until t = T:
                2a. All stones that jumped to this t in phase 1 are added to the board, and are causally free
                2b. Every player declares a single spatial move for one of their causally free stones (if they have any), and the moves are executed simultaneously
                2c. t increases by 1
            3. When the clock reaches T, the CAUSAL CONSISTENCY CALCULATOR selects a self-consistent version of the board history and presents it to the players.
                At this point, if any of the game over conditions is met, the game ends and a winner is declared.
        """
        
        #stone lines are volatile so we dont need to store them (use flags)
        #we DO need to keep track of the causally free stones tho
        
        self.round_number = 0
        while(True):
            # PHASE 1
            if self.round_number > 0:
                print("Select causally free stones to travel back in time HERE")
            # PHASE 2
            for t in range(self.T - 1):
                # bring the board to t
                self.execute_moves()#t + 2) # shouldnt this be the whole thing, so we see which stones are causally linked to the future??
                self.print_board_at_time(t)
                #self.print_board_horizontally()
                
                # add one spatial move per player
                for faction in self.factions:
                    while(True):
                        try:
                            player_move_raw = input(f"Player {faction}, input your move at t = {t} in the form \"x1 y1 fwd/bwd/turn a2\": ")
                            if player_move_raw in 'exit':
                                return(-1)
                            player_move_list = player_move_raw.split(' ')
                            pos0 = (int(player_move_list[0]), int(player_move_list[1]))
                            target_stone = self.find_stone_at_position(t + 1, pos0)
                            if target_stone == -1:
                                print(f"No stone found at the specified position {pos0}. Try again.")
                                continue
                            # if no a1 specified, a0 is preserved
                            if len(player_move_list) < 4:
                                player_move_list.append(target_stone.get_azimuth(t+1))
                            pos1, a1 = decode_tank_controls(pos0, target_stone.get_azimuth(t+1), *player_move_list[2:])
                            add_move_msg = self.add_spatial_move(t + 1, pos0, pos1, a1, faction)
                            if add_move_msg == -1:
                                print("Illegal move. Try again.")
                            else:
                                break
                        except:
                            print("Your input couldn't be parsed")
                # a move at t means that all the stones that were causally free at t are now linked to t+1 and they're causally free at t
                """for faction in self.factions:
                    for stone in self.stones[faction]:
                        stone.progress_causal_freedom(t+1, self.T)"""
