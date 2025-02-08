# -----------------------------------------------------------------------------
# ------------------------------ class Scenario -------------------------------
# -----------------------------------------------------------------------------
# An instance of this class for a given Gamemaster instance defines the
# activity maps for setup flags and effect flags, and stores trackers.

class Scenario():

    def __init__(self, setup_activity_map, effect_activity_map, effect_cause_map, stone_inheritance):
        self.setup_activity_map = setup_activity_map
        self.effect_activity_map = effect_activity_map
        self.effect_cause_map = effect_cause_map
        self.stone_inheritance = stone_inheritance

