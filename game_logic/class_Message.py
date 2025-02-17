
# ---------------------------------------------
# --------------- class Message ---------------
# ---------------------------------------------
# A simple structure where every instance encodes a function log

class Message():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, header, msg = ""):
        self.header = header
        self.msg = msg

    def __str__(self):
        if self.msg == "":
            return(f"empty Message '{self.header}'")
        return(f"Message '{self.header}': \"{self.msg}\"")
    def __repr__(self):
        return(self.__str__())
