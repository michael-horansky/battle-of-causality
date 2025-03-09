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
        # ------------------------ General properties -------------------------
        self.board_static = None
        self.t_dim = None
        self.x_dim = None
        self.y_dim = None

        self.factions = []
        self.faction_armies = [] # ["faction"] = [stone_ID list]
        self.number_of_turns = None
        # ------------------------ Turnwise properties ------------------------
        # These variables always have the first axis [turn index], and describe
        # the state of the game as said turn BEGINS (is equal to current_turn).
        self.stone_trajectories = [] # [turn][t]["process"][stone_ID] = state, where "process" specifies which part of the turn this state describes
        self.stone_endpoints = [] #[turn][stone_ID] = {"start" : desc, "end" : desc} or None
        self.canonised_stone_trajectories = [] # [round_number][t]["process"][stone_ID] = state; this is used for the omit-ante-effects scenes which are found at the end of each round.
        self.canonised_stone_endpoints = []

        self.active_turn = None


    # -------------------------------------------------------------------------
    # ---------------------- General property management ----------------------
    # -------------------------------------------------------------------------

    def set_board_dimensions(self, t_dim, x_dim, y_dim):
        self.t_dim = t_dim
        self.x_dim = x_dim
        self.y_dim = y_dim

    def set_board_static(self, board_static):
        self.board_static = board_static # [x][y] = square string rep

    def record_faction_armies(self, factions, faction_armies):
        self.factions = factions
        self.faction_armies = faction_armies

    def record_number_of_turns(self, number_of_turns):
        self.number_of_turns = number_of_turns

    # -------------------------------------------------------------------------
    # --------------------- Turnwise property management ----------------------
    # -------------------------------------------------------------------------

    # ------------------------- Resets at turn start --------------------------

    def reset_turn(self, turn):
        # Prepares all variables to contain turn key
        if len(self.stone_trajectories) > turn:
            # key exists
            self.stone_trajectories[turn] = []
            for t in range(self.t_dim):
                self.stone_trajectories[turn].append({})
                for process_key in Abstract_Output.process_list:
                    self.stone_trajectories[turn][t][process_key] = {}
        else:
            # We keep appending empty turns until key exists
            while(len(self.stone_trajectories) <= turn):
                self.stone_trajectories.append([])
                for t in range(self.t_dim):
                    self.stone_trajectories[-1].append({})
                    for process_key in Abstract_Output.process_list:
                        self.stone_trajectories[-1][t][process_key] = {}

        if len(self.stone_endpoints) > turn:
            # key exists
            self.stone_endpoints[turn] = {}
        else:
            while(len(self.stone_endpoints) <= turn):
                self.stone_endpoints.append({})

    def reset_canonised_round(self, canonised_round):
        # Prepares all variables to contain turn key
        if len(self.canonised_stone_trajectories) > canonised_round:
            # key exists
            self.canonised_stone_trajectories[canonised_round] = []
            for t in range(self.t_dim):
                self.canonised_stone_trajectories[canonised_round].append({})
                for process_key in Abstract_Output.process_list:
                    self.canonised_stone_trajectories[canonised_round][t][process_key] = {}
        else:
            # We keep appending empty turns until key exists
            while(len(self.canonised_stone_trajectories) <= canonised_round):
                self.canonised_stone_trajectories.append([])
                for t in range(self.t_dim):
                    self.canonised_stone_trajectories[-1].append({})
                    for process_key in Abstract_Output.process_list:
                        self.canonised_stone_trajectories[-1][t][process_key] = {}

        if len(self.canonised_stone_endpoints) > canonised_round:
            # key exists
            self.canonised_stone_endpoints[canonised_round] = {}
        else:
            while(len(self.canonised_stone_endpoints) <= canonised_round):
                self.canonised_stone_endpoints.append({})

    # --------------------------- Value assignment ----------------------------

    def add_empty_trajectory(self, turn, stone_ID):
        for t in range(self.t_dim):
            for process_key in Abstract_Output.process_list:
                self.stone_trajectories[turn][t][process_key][stone_ID] = None
        self.stone_endpoints[turn][stone_ID] = None

    def add_empty_canonised_trajectory(self, canonised_round, stone_ID):
        for t in range(self.t_dim):
            for process_key in Abstract_Output.process_list:
                self.canonised_stone_trajectories[canonised_round][t][process_key][stone_ID] = None
        self.canonised_stone_endpoints[canonised_round][stone_ID] = None

    def add_stone_endpoint(self, turn, stone_ID, endpoint_key, endpoint_value):
        if self.stone_endpoints[turn][stone_ID] is None:
            self.stone_endpoints[turn][stone_ID] = {endpoint_key : endpoint_value}
        else:
            self.stone_endpoints[turn][stone_ID][endpoint_key] = endpoint_value

    def add_canonised_stone_endpoint(self, canonised_round, stone_ID, endpoint_key, endpoint_value):
        if self.canonised_stone_endpoints[canonised_round][stone_ID] is None:
            self.canonised_stone_endpoints[canonised_round][stone_ID] = {endpoint_key : endpoint_value}
        else:
            self.canonised_stone_endpoints[canonised_round][stone_ID][endpoint_key] = endpoint_value


    def set_active_turn(self, active_turn):
        self.active_turn = active_turn


