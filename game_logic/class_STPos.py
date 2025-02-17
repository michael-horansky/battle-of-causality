
import utils.constants as constants

# ---------------------------------------------
# ---------------- class STPos ----------------
# ---------------------------------------------
# A simple structure where every instance encodes a single spacetime position

class STPos():

    # --------------- class methods ----------------
    @classmethod
    def from_str(cls, str_repr):
        new_args = str_repr[1:-1].split(constants.STPos_delim)
        try:
            t = int(new_args[0])
            x = int(new_args[1])
            y = int(new_args[2])
            return(cls(t, x, y))
        except:
            print(f"STPos(repr) attempted initialization from a badly formatted string representation: {t}")
            return(-1)

    # --- Constructors, destructors, descriptors ---
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y

    """def __str__(self):
        return(f"{{t:{self.t}, x:{self.x}, y:{self.y}}}")
    def __repr__(self):
        return(self.__str__())"""

    # The __str__ overload is used when converting to dynamic representations
    # in flag_args, and thus must be standardised

    def __str__(self):
        return("(" + (constants.STPos_delim).join(str(x) for x in [self.t, self.x, self.y]) + ")")

    # --- Stepping methods ---
    def step(self, azimuth):
        if azimuth == 0:
            self.y -= 1
        if azimuth == 1:
            self.x += 1
        if azimuth == 2:
            self.y += 1
        if azimuth == 3:
            self.x -= 1
