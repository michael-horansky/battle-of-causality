from functools import cmp_to_key

from class_Message import Message

# -----------------------------------------------------------------------------
# ------------------------ class Activity_map_iterator ------------------------
# -----------------------------------------------------------------------------
# An instance of this class for a given Gamemaster instance iterates through
# the space of all available activity maps in descending priority order based
# on the lexicographic order

class Activity_map_iterator():

    @staticmethod
    def compare_states_by_recency(A, B):
        # The highest-index point of difference: higher False means larger (further down in descending priority)
        for i in range(len(A) - 1, -1, -1):
            if A[i] != B[i]:
                if A[i] == False:
                    return(1)
                if B[i] == False:
                    return(-1)
        return(0)

    @staticmethod
    def cartesian_product(A, B):
        # Takes two lists of lengths x and y, where the elements are lists of lengths m and n,
        # and returns a list of length x.y where elements are lists of length m+n
        result = []
        for i in range(len(A)):
            for j in range(len(B)):
                result.append(A[i] + B[j])
        return(result)

    def __init__(self, number_of_switches, specification):
        # Number of switches will be equal to number of flags in the subset we
        # iterate through in a Gamemaster routine
        self.number_of_switches = number_of_switches
        # Priority representation options:
        #   "recency" : Deactivating lower-index switches takes priority
        #   "conservation" : A smaller number of deactivations takes priority
        if isinstance(specification, str):
            self.priority_representation = specification
            self.fix_number_of_deactivations = None
        elif isinstance(specification, int):
            self.priority_representation = "conservation"
            self.fix_number_of_deactivations = specification

        self.reset_current_state()

    def read_current_state(self):
        return(self.current_state.copy())

    def reset_current_state(self):
        if self.fix_number_of_deactivations is None:
            self.current_state = [True] * self.number_of_switches
            self.current_number_of_deactivations = 0
        else:
            self.current_state = [False] * self.fix_number_of_deactivations + [True] * (self.number_of_switches - self.fix_number_of_deactivations)
            self.current_number_of_deactivations = self.fix_number_of_deactivations

    def terminate_state(self):
        self.current_state = None
        self.current_number_of_deactivations = None
        return(Message("termination"))

    def next_state(self):
        # This method returns a Message()
        if self.current_state is None:
            return(Message("last_state_reached"))
        if self.current_state == [False] * self.number_of_switches:
            return(self.terminate_state())

        if self.priority_representation == "recency":
            for i in range(self.number_of_switches):
                if self.current_state[i] == True:
                    self.current_state[i] = False
                    break
                else:
                    self.current_state[i] = True
            if self.current_state == [False] * self.number_of_switches:
                return(Message("last_state_reached"))
            return(Message("OK"))
        if self.priority_representation == "conservation":
            if self.current_number_of_deactivations == 0:
                self.current_number_of_deactivations = 1
                self.current_state = [False] * self.current_number_of_deactivations + [True] * (self.number_of_switches - self.current_number_of_deactivations)
                if self.fix_number_of_deactivations is not None and self.current_number_of_deactivations != self.fix_number_of_deactivations:
                    return(self.terminate_state())
                if self.current_number_of_deactivations == self.number_of_switches:
                    return(Message("last_state_reached"))
                return(Message("raised_number_of_deactivations"))
            number_of_passed_ons = 0
            pointer_index = 0
            while(self.current_state[pointer_index] == True):
                number_of_passed_ons += 1
                pointer_index += 1
                if number_of_passed_ons == self.number_of_switches - self.current_number_of_deactivations:
                    self.current_number_of_deactivations += 1
                    self.current_state = [False] * self.current_number_of_deactivations + [True] * (self.number_of_switches - self.current_number_of_deactivations)
                    if self.fix_number_of_deactivations is not None and self.current_number_of_deactivations != self.fix_number_of_deactivations:
                        return(self.terminate_state())
                    if self.current_number_of_deactivations == self.number_of_switches:
                        return(Message("last_state_reached"))
                    return(Message("raised_number_of_deactivations"))
            while(self.current_state[pointer_index] == False):
                pointer_index += 1
            self.current_state = [False] * (pointer_index - 1 - number_of_passed_ons) + [True] * (number_of_passed_ons + 1) + [False] + self.current_state[pointer_index+1:]

    def get_span(self):
        self.reset_current_state()
        res = []
        while(self.current_state is not None):
            res.append(self.read_current_state())
            self.next_state()
        self.reset_current_state()
        return(res)

