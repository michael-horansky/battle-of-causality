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
        # ----------------------- Roundwise properties ------------------------
        # These variables always have the first axis [round number], and
        # describe the state of the game in the canonised version of the round,
        # or (for the last value) the state of the game as current_turn begins.
        self.stone_trajectories = [] # [round_number][t]["process"][stone_ID] = state, where "process" specifies which part of the round this state describes
        self.stone_endpoints = [] #[round_number][stone_ID] = {"start" : desc, "end" : desc} or None

        self.stone_actions = [] # [round_number][t][action index] = [stone_type, action_type, stone_x, stone_y, param1, param2...]

        self.time_jumps = [] # [round_number]["t"]["x"]["y"]["used"/"unused"] = "TJI"/"TJO"/"conflict" if present

        self.current_turn = None


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
    # --------------------- Roundwise property management ---------------------
    # -------------------------------------------------------------------------

    # --------------- Resets at the beginning of execute_moves ----------------

    def reset_round(self, round_n):
        # Prepares all variables to contain round_n key
        if len(self.stone_trajectories) > round_n:
            # key exists
            self.stone_trajectories[round_n] = []
            for t in range(self.t_dim):
                self.stone_trajectories[round_n].append({})
                for process_key in Abstract_Output.process_list:
                    self.stone_trajectories[round_n][t][process_key] = {}
        else:
            # We keep appending empty turns until key exists
            while(len(self.stone_trajectories) <= round_n):
                self.stone_trajectories.append([])
                for t in range(self.t_dim):
                    self.stone_trajectories[-1].append({})
                    for process_key in Abstract_Output.process_list:
                        self.stone_trajectories[-1][t][process_key] = {}

        if len(self.stone_endpoints) > round_n:
            # key exists
            self.stone_endpoints[round_n] = {}
        else:
            while(len(self.stone_endpoints) <= round_n):
                self.stone_endpoints.append({})

        if len(self.stone_actions) > round_n:
            # key exists
            self.stone_actions[round_n] = []
            for t in range(self.t_dim):
                self.stone_actions[round_n].append([])
        else:
            # We keep appending empty turns until key exists
            while(len(self.stone_actions) <= round_n):
                self.stone_actions.append([])
                for t in range(self.t_dim):
                    self.stone_actions[-1].append([])

        if len(self.time_jumps) > round_n:
            # key exists
            self.time_jumps[round_n] = {}
        else:
            # We keep appending empty turns until key exists
            while(len(self.time_jumps) <= round_n):
                self.time_jumps.append({})

    # --------------------------- Value assignment ----------------------------

    def add_empty_trajectory(self, round_n, stone_ID):
        for t in range(self.t_dim):
            for process_key in Abstract_Output.process_list:
                self.stone_trajectories[round_n][t][process_key][stone_ID] = None
        self.stone_endpoints[round_n][stone_ID] = None

    def add_stone_endpoint(self, round_n, stone_ID, endpoint_key, endpoint_value):
        if self.stone_endpoints[round_n][stone_ID] is None:
            self.stone_endpoints[round_n][stone_ID] = {endpoint_key : endpoint_value}
        else:
            self.stone_endpoints[round_n][stone_ID][endpoint_key] = endpoint_value

    def add_stone_action(self, round_n, t, action_array):
        self.stone_actions[round_n][t].append(action_array.copy())

    def add_time_jump(self, round_n, t, x, y, is_used, time_jump_type):
        if t not in self.time_jumps[round_n].keys():
            self.time_jumps[round_n][t] = {}
        if x not in self.time_jumps[round_n][t].keys():
            self.time_jumps[round_n][t][x] = {}
        if y not in self.time_jumps[round_n][t][x].keys():
            self.time_jumps[round_n][t][x][y] = {}
        if is_used not in self.time_jumps[round_n][t][x][y].keys():
            self.time_jumps[round_n][t][x][y][is_used] = time_jump_type
        elif self.time_jumps[round_n][t][x][y][is_used] not in [time_jump_type, "conflict"]:
            self.time_jumps[round_n][t][x][y][is_used] = "conflict"



    def set_current_turn(self, current_turn):
        self.current_turn = current_turn


