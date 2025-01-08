
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
