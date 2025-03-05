# -----------------------------------------------------------------------------
# --------------------------- class Abstract_Output ---------------------------
# -----------------------------------------------------------------------------
# An instance is created by GM and fed into any Renderer-type class instance
# Encodes both static and interactive elements of the game state

class Abstract_Output():

    process_list = [
            "flags",        # State of board after naive flagh execution
            "pushes",       # State of board after sokoban pushes, opposition, and impasses
            "destructions", # State of board after captures and explosions
            "tagscreens",   # State of board after tagscreens
            "canon"         # State of board after stone and board actions (e.g. attacks)
        ]

    def __init__(self, board_static, board_entities):
        self.board_static = board_static # [x][y] = square string rep
        self.board_entities = board_entities # [list of [t]["process"] = state], where "process" specifies which part of the turn this state dexcribes ()

