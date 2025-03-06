# -----------------------------------------------------------------------------
# --------------------------- class Abstract_Output ---------------------------
# -----------------------------------------------------------------------------
# An instance is created by GM and fed into any Renderer-type class instance
# Encodes both static and interactive elements of the game state

import utils.constants as constants
import utils.functions as functions

class Abstract_Output():

    process_list = [
            "flags",        # State of board after naive flagh execution
            "pushes",       # State of board after sokoban pushes, opposition, and impasses
            "destructions", # State of board after captures and explosions
            "tagscreens",   # State of board after tagscreens
            "canon"         # State of board after stone and board actions (e.g. attacks)
        ]

    def __init__(self):
        self.board_static = None
        # ------------------------ Turnwise properties ------------------------
        # These variables always have the first axis [turn index], and describe
        # the state of the game as said turn BEGINS (is equal to current_turn).
        self.board_stones = [] # [turn][t]["process"][stone_ID] = state, where "process" specifies which part of the turn this state describes

    def set_board_dimensions(self, t_dim, x_dim, y_dim):
        self.t_dim = t_dim
        self.x_dim = x_dim
        self.y_dim = y_dim

    def set_board_static(self, board_static):
        self.board_static = board_static # [x][y] = square string rep

    def reset_turn(self, turn):
        # Prepares all variables to contain turn key
        if len(self.board_stones) > turn:
            # key exists
            self.board_stones[turn] = []
            for t in range(self.t_dim):
                self.board_stones[turn].append({})
                for process_key in Abstract_Output.process_list:
                    self.board_stones[turn][t][process_key] = []
        else:
            # We keep appending empty turns until key exists
            while(len(self.board_stones) <= turn):
                self.board_stones.append([])
                for t in range(self.t_dim):
                    self.board_stones[-1].append({})
                    for process_key in Abstract_Output.process_list:
                        self.board_stones[-1][t][process_key] = []

