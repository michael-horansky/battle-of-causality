# This is a document with all the typographical and numerical constants which need to be consistent across all the game files

# -----------------------------------------------------------------------------
# -------------------------- Typographical constants --------------------------
# -----------------------------------------------------------------------------

# -------------------------------- Delimiters ---------------------------------
# Since representations have to be nested, these delimiters have to be unique!
STPos_delim = ","
Flag_delim = ":"
Gamemaster_delim = ";"



# ----------------------------- Legacy constants ------------------------------
stone_type_representations = {
        "T" : ["A", "tank"],
        "L" : ["B", "tank"],
        "Y" : ["A", "bombardier"],
        "V" : ["B", "bombardier"]
    }

stone_symbols = {
        "A" : {
                "tank" : "T",
                "bombardier" : "Y"
            },
        "B" : {
                "tank" : "L",
                "bombardier" : "V"
            }
    }


base_representations = {
        "A" : "A",
        "B" : "B",
        "!" : "neutral"
    }

base_symbols = {
        "A" : "A",
        "B" : "B",
        "neutral" : "!"
    }
