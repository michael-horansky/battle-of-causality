
# ---------------------------------------------
# --------------- class Message ---------------
# ---------------------------------------------
# A simple structure where every instance encodes a function log

class Message():
    # --- Constructors, destructors, descriptors ---
    def __init__(self, msg_header, msg):
        self.msg_header = msg_header
        self.msg = msg

    def __str__(self):
        return(f"Message '{self.msg_header}': \"{self.msg}\"")
    def __repr__(self):
        return(self.__str__())
