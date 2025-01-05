

import math
from class_Stone import *

# ---------------------------------------------
# ---------------- class STPos ----------------
# ---------------------------------------------

class STPos():
    # A simple structure where every instance encodes a single spacetime position
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y

    def __str__(self):
        return(f"\{t:{self.t}, x:{self.x}, y:{self.y}\}")
    def __repr__(self):
        return(self.__str__())


# ---------------------------------------------
# ------------ class Board_square -------------
# ---------------------------------------------

class Board_square():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, pos):
        self.pos = pos
        self.stones = [] # list of IDs which always has to be of length 1 or 0
        self.stone_properties = [] # [azimuth, ...]
        self.flags = [] # this list can be long

# ---------------------------------------------
# ------------- class Gamemaster --------------
# ---------------------------------------------

class Gamemaster():
    # --- Constructors, destructors, descriptors ---



