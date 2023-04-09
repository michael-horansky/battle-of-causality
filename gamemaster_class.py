

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
        return([-1] * (t) + [pos])

        

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
        if self.move_type == 'time_jump_out':
            str_rep = f"Time jump OUT (P. '{self.player_faction}', ID {self.stone_ID}): at {self.pos}, jump into {self.move_args[0]}"
        if self.move_type == 'time_jump_in':
            str_rep = f"Time jump IN (P. '{self.player_faction}', ID {self.stone_ID}): at {self.pos}"
        if self.move_type == 'spatial_move':
            str_rep = f"Spatial move (P. '{self.player_faction}', ID {self.stone_ID}): {self.pos} -> {self.move_args[0]} [{human_readable_azimuth(self.move_args[1])}]"
        if self.move_type == 'attack':
            str_rep = f"Attack (P. '{self.player_faction}', ID {self.stone_ID}): at {self.pos}"
        
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
            # args = [is_active, azimuth]
            return(self.move_args[0], self.move_args[1])
        if self.move_type == 'spatial_move':
            # args = [pos_target, a_target]
            return(self.move_args[0], self.move_args[1])
        if self.move_type == 'attack':
            # args = [allow_friendly_fire]
            return(self.move_args[0])

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
        self.flag_types = ['add_stone', 'time_jump_out', 'time_jump_in', 'spatial_move', 'attack'] #the order matters in here, actually! spawns first, then moves and shootings
        self.history = []
        self.causal_freedom_progression_list = [] # [t] = [ID1, ID2...]
        # self.history[time] = {'add_stone' : [add_stone1, add_stone2...], 'spatial_move' : [move1, move2...]}
        self.setup_moves = []
        
        self.which_t_just_progressed  = -1
        
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
        self.causal_freedom_progression_list = []
        for t in range(self.T):
            self.history.append({})
            for flag_type in self.flag_types:
                self.history[t][flag_type] = []
            self.causal_freedom_progression_list.append([])
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
        
    
    def is_pos_available(self, t, pos0, pos1, player_faction = -1, allow_box_pushing = True, generating_move = -1):
        # TODO switch the argument to just the board_move, i reckon
        approach_azimuth = get_azimuth_from_delta_pos(pos0, pos1)
        if not self.is_board_symbol_available(self.get_square(pos1)):
            return(False)
        if self.find_stone_at_position(t, pos1, player_faction = player_faction, debug_msg = False) != -1:
            return(False)
        
        for stone_generating_move_type in board_move.stone_generating_move_types:
            for move in self.history[t][stone_generating_move_type]:
                print("LALALA", move, "HOHOHO", generating_move)
                if generating_move != move:
                    print("||||", move.pos, pos1, move.pos == pos1)
                    if move.pos == pos1:
                        print("generating move conflicf")
                        return(False)
                    # a stone will be spawned in here
        
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
    
    def find_stone_in_direction(self, t, pos, a, terminate_at_wall = True):
        cur_pos = pos
        while(True):
            cur_pos = pos_step(cur_pos, a)
            if (not self.is_board_symbol_available(self.get_square(cur_pos))) and terminate_at_wall:
                return(-1)
            target_stone = self.find_stone_at_position(t, cur_pos, debug_msg = False)
            if target_stone != -1:
                return(target_stone)
        
    
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
                # dont copy if the stone just died
                if t in stone.events['death'] or t in stone.events['time_jump']:
                    #stone.position[t+1] = -1 #is this line even needed? or maybe for clarity?
                    continue
                if stone.is_causally_free(t):
                    continue #we don't know where it'll go
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
        #if not (pos0 == pos1 or self.is_pos_available(t, pos0, pos1, player_faction = player_faction, allow_box_pushing = True)):
        if not self.is_board_symbol_available(self.get_square(pos1)):
            print("  Can't move into the wall.")
            return(-1)
        if player_faction != -1 and target_stone.player_faction != player_faction:
            return(-1)
        if not target_stone.is_causally_free(t):
            return(-1)
        self.history[t]['spatial_move'].append(board_move('spatial_move', self.round_number, target_stone.player_faction, pos0, [pos1, a1], target_stone.ID))
        return(0)
    
    def add_attack(self, t, attacking_stone, allow_friendly_fire = True):
        pos = attacking_stone.get_position(t)
        print("YOHOOOO")
        self.history[t]['attack'].append(board_move('attack', self.round_number, attacking_stone.player_faction, pos, [allow_friendly_fire], attacking_stone.ID))
        print("HRHLIUGL")
        return(0)
                    
    
    def add_time_jump(self, pos, azimuth, t0, t1, player_faction = -1):
        # adds a time jump out, a time jump in, and sets the found stone as causally non-free
        target_stone = self.find_stone_at_position(t0, pos)
        if target_stone == -1:
            return(-1)
        if not (self.is_pos_available(t1, pos, pos, player_faction = player_faction, allow_box_pushing = False)):
            return(-1)
        if player_faction != -1 and target_stone.player_faction != player_faction:
            return(-1)
        if not target_stone.is_causally_free(t0):
            return(-1)
        
        
        
        time_jump_out_move = board_move('time_jump_out', self.round_number, player_faction, pos, [t1], target_stone.ID)
        time_jump_in_move  = board_move('time_jump_in' , self.round_number+1, player_faction, pos, [True, azimuth])
        
        self.history[t0]['time_jump_out'].append(time_jump_out_move)
        self.history[t1]['time_jump_in' ].append(time_jump_in_move )
        
        target_stone.events['time_jump'].append(t0)
        return(0)
        
        # self.time_jump_stone(pos, t0, t1, player_faction)
    
    
    
    def resolve_conflicts(self, t, allow_stone_pushing = True, stone_push_locations = []):
        # this function takes a realised board at time t and changes it so that no space is occupied by more than 1 stone
        # and no stone is on a forbidden space.
        # it assumes the board is conflict-less at t-1
        # it should eventually fully replace the clunky is_pos_available checking
        
        conflict_encountered = False
        encountered_stone_push_locations = []
        # First, we find positions where multiple stones conflict
        unchecked_stones = []
        for faction in self.factions:
            for stone in self.stones[faction]:
                unchecked_stones.append(stone)
        for x in range(self.x_dim):
            for y in range(self.y_dim):
                stones_here = []
                i = 0
                while(i < len(unchecked_stones)):
                    if unchecked_stones[i].get_position(t) == (x, y):
                        stones_here.append(unchecked_stones.pop(i))
                    else:
                        i += 1
                if len(stones_here) > 1:
                    # conflict here!
                    conflict_encountered = True
                    # if length == 2, we attempt a sokoban push; otherwise, we move all stones to where they came from
                    # to forbid chaining, sokoban pushing is only attempted on the first iteration or if such solution was already used here in a previous iteration
                    if len(stones_here) == 2 and ((x, y) in stone_push_locations or allow_stone_pushing):
                        approach_azimuth_1 = get_azimuth_from_delta_pos(stones_here[0].get_position(t - 1), stones_here[0].get_position(t))
                        approach_azimuth_2 = get_azimuth_from_delta_pos(stones_here[1].get_position(t - 1), stones_here[1].get_position(t))
                        if approach_azimuth_1 == -1:
                            pos_to_push_into = pos_step((x, y), approach_azimuth_2)
                            if self.is_board_symbol_available(self.get_square(pos_to_push_into)):
                                # first stone gets pushed
                                encountered_stone_push_locations.append((x, y))
                                stones_here[0].position[t] = pos_to_push_into
                                continue
                        elif approach_azimuth_2 == -1:
                            pos_to_push_into = pos_step((x, y), approach_azimuth_1)
                            if self.is_board_symbol_available(self.get_square(pos_to_push_into)):
                                # second stone gets pushed
                                encountered_stone_push_locations.append((x, y))
                                stones_here[1].position[t] = pos_to_push_into
                                continue
                    # all stones return where they came from
                    for j in range(len(stones_here)):
                        stones_here[j].position[t] = stones_here[j].get_position(t-1)
        # If no conflict encountered, we exit. Otherwise, we call itself:
        if conflict_encountered == False:
            return(0)
        else:
            return(self.resolve_conflicts(t, False, encountered_stone_push_locations))
    
    
    
    def execute_moves(self, max_t = -1, exit_on_illegal_move = False):
        # resets the board, executes all the moves in order: transforms history into stone evolution
        if max_t == -1:
            max_t = self.T
        self.reset_board()
        for t in range(max_t):
            if t > 0:
                self.copy_board_onto_next_t(t - 1)
            # TODO SIMULTANEOUS CONFLICT RESOLUTION!!! (what if two stones want to go to the same spot at the same time? first come first serve is bad)
            
            for add_stone_move in self.history[t]['add_stone']:
                pos_0 = get_position_list_for_spawn(t, add_stone_move.pos)
                a_0   = get_position_list_for_spawn(t, add_stone_move.move_args[0])
                #print("keheeee", stone)
                self.stones[add_stone_move.player_faction].append(Stone(add_stone_move.stone_ID, add_stone_move.round_number, add_stone_move.player_faction, pos_0, a_0))
                
            # TODO for the time jumps, we need to implement the PICK A CONSISTENT HISTORY SCENARIO
            for time_jump_out_move in self.history[t]['time_jump_out']:
                target_stone = self.find_stone_at_position(t, spatial_move.pos)
                if target_stone == -1:
                    if exit_on_illegal_move:
                        print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                        return(-1)
                    continue
                # NOTE time jumping should be anonymous!!
                target_stone.events['time_jump'].append(t)
            
            for time_jump_in_move in self.history[t]['time_jump_in']:
                pos_0 = get_position_list_for_spawn(t, time_jump_in_move.pos)
                a_0   = get_position_list_for_spawn(t, time_jump_in_move.move_args[1])
                self.stones[time_jump_in_move.player_faction].append(Stone(time_jump_in_move.stone_ID, time_jump_in_move.round_number, time_jump_in_move.player_faction, pos_0, a_0))
                
            
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
                target_stone.position[t] = pos1
                if a1 != -1:
                    target_stone.azimuth[t] = a1
            
            # Resolve conflicts
            self.resolve_conflicts(t)
            
            # The stones are now in place. Resolve attacks now.
            for attack in self.history[t]['attack']:
                attacking_stone = self.find_stone_at_position(t, attack.pos)
                if attacking_stone == -1:
                    if exit_on_illegal_move:
                        print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                        return(-1)
                    continue
                if attacking_stone.ID != attack.stone_ID:
                    if exit_on_illegal_move:
                        print("gamemaster.execute_moves routine ended due to illegal move flagged as an exit condition")
                        return(-1)
                    continue
                target_stone = self.find_stone_in_direction(t, attack.pos, attacking_stone.get_azimuth(t), terminate_at_wall = True)
                if target_stone != -1:
                    # we shot something
                    
                    # check if frienndly fire applicable and allowed:
                    if not(attack.move_args[0] == False and target_stone.player_faction == attacking_stone.player_faction):
                        target_stone.events['death'].append(t)
            
            # Update causal freedom
            causally_affected_stones = self.get_stones_by_IDs(self.causal_freedom_progression_list[t])
            for stone in causally_affected_stones:
                stone.progress_causal_freedom(t, self.T, 1000)
    
    
    # ----------------------------------------------------
    # --------------- game loop functions ----------------
    # ----------------------------------------------------
    
    def get_stones_by_IDs(self, ID_list):
        result_list = []
        for faction in self.factions:
            for stone in self.stones[faction]:
                if stone.ID in ID_list:
                    result_list.append(stone)
        return(result_list)
    
    def mark_causally_free_stones(self, t):
        # adds all stone IDs of stones that are causally free at t ATM to causal_freedom_progression_list
        for faction in self.factions:
            for stone in self.stones[faction]:
                if stone.is_causally_free(t) and not (stone.ID in self.causal_freedom_progression_list[t]):
                    self.causal_freedom_progression_list[t].append(stone.ID)
    
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
        
        
        self.round_number = -1
        self.which_t_just_progressed = 0
        while(True):
            
            self.round_number += 1
            
            # PHASE 1
            if self.round_number > 0:
                print("Select causally free stones to travel back in time HERE")
            
            
            print(self.history)
            # PHASE 2
            for t in range(self.T - 2):
                # bring the board to t-1
                self.which_t_just_progressed = t
                self.execute_moves()#t + 2) # shouldnt this be the whole thing, so we see which stones are causally linked to the future??
                #self.print_board_at_time(t+1)
                self.print_board_horizontally()
                
                # add one spatial move per player
                for faction in self.factions:
                    while(True):
                        try:
                            select_stone_pos_raw = input(f"Player {faction}, select a stone at t = {t+1} by inputting its position (\"x1 y1\"): ")
                            if select_stone_pos_raw in ['']:
                                break # pass
                            if select_stone_pos_raw in ['exit']:
                                return(-1) # exit the program
                            select_stone_pos = (int(select_stone_pos_raw.split(' ')[0]), int(select_stone_pos_raw.split(' ')[1]))
                            target_stone = self.find_stone_at_position(t + 1, select_stone_pos)
                            if target_stone == -1:
                                print(f"  No stone found at the specified position {select_stone_pos}. Try again.")
                                continue
                            if faction != target_stone.player_faction:
                                print("  Selected stone doesn't belong to your faction. Try again.")
                                continue
                            if not target_stone.is_causally_free(t+1):
                                print("  Selected stone is not causally free. Try again.")
                                continue
                            
                            move_msg = target_stone.parse_move_cmd(self, t+1)
                            if move_msg == -1:
                                # move failed
                                #print("  Your move is illegal. Try again")
                                continue
                            else:
                                break
                            
                            """player_move_raw = input(f"Player {faction}, input your move at t = {t+1} in the form \"x1 y1 fwd/bwd/turn/atk a2\": ")
                            #TODO: different pieces would have different mechanics. first select a stone by position, then do its sequence of move adding
                            # for standard tanks, this is either move or fire
                            if player_move_raw in '':
                                break
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
                                break"""
                        except:
                            print("Your input couldn't be parsed")
                self.mark_causally_free_stones(t+1)
                # a move at t means that all the stones that were causally free at t are now linked to t+1 and they're causally free at t
                """for faction in self.factions:
                    for stone in self.stones[faction]:
                        stone.progress_causal_freedom(t+1, self.T)"""
            
            # WE ARE NOW AT t = T-1, and it's time to select causally free stones that will travel back in time
            t = self.T - 2
            self.which_t_just_progressed = t
            self.execute_moves()
            self.print_board_at_time(t)
            for faction in self.factions:
                print(f"Player {faction}, you will now select the stones that will travel back in time.")
                while(True):
                    #try:
                    player_move_raw = input(f"  Select a stone in the form \"x y target_time\" (empty input finalizes selection): ")
                    if player_move_raw == 'exit':
                        return(-1)
                    if player_move_raw == '':
                        break
                    player_move_list = player_move_raw.split(' ')
                    pos0 = (int(player_move_list[0]), int(player_move_list[1]))
                    target_stone = self.find_stone_at_position(t, pos0)
                    if target_stone == -1:
                        print(f"No stone found at the specified position {pos0}. Try again.")
                        continue
                    if not target_stone.is_causally_free(t+1):
                        print("Selected stone not causally free")
                        continue
                    # if no target time specified, it is set to 0
                    if len(player_move_list) < 3:
                        player_move_list.append(0)
                    
                    add_move_msg = self.add_time_jump(pos0, target_stone.get_azimuth(t+1), t + 1, int(player_move_list[2]), faction)
                    if add_move_msg == -1:
                        print("Illegal move. Try again.")
                        #else:
                        #    break
                    #except:
                    #    print("Your input couldn't be parsed")
