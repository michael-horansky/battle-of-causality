
import numpy as np

# Automatic string trimming
def uniform_str(x, l=3, pad_c='0'):
    x_str = str(x)
    return(pad_c*(l-len(x_str))+x_str)

# Centered string of length w
def st(a, w, f = ' '):
    if len(str(a)) >= w:
        return(str(a))
    else:
        diff = w - len(str(a))
        return(f * int(np.floor(diff / 2.0)) + str(a) + f * int(np.ceil(diff / 2.0)))

# This generates a list [element, element, element...]
def repeated_list(length, element=''):
    result = []
    if isinstance(element, list) or isinstance(element, dict):
        for i in range(length):
            result.append(element.copy())
    else:
        for i in range(length):
            result.append(element)
    return(result)

def add_tail_to_list(old_list, new_length, tail_element = []):
    while(len(old_list) < new_length):
        old_list.append(tail_element.copy())
    return(old_list)

def get_delta_pos_step(pos, azimuth):
    if cur_a == 0:
        return(0, -1)
    if cur_a == 1:
        return(1, 0)
    if cur_a == 2:
        return(0, 1)
    if cur_a == 3:
        return(-1, 0)

# find the position in our convention that is one step from pos in the direction azimuth
def pos_step(pos, azimuth):
    x, y = pos
    if azimuth == 0:
        return((x, y-1))
    if azimuth == 1:
        return((x+1, y))
    if azimuth == 2:
        return((x, y+1))
    if azimuth == 3:
        return((x-1, y))

def get_azimuth_from_delta_pos(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    if x2 == x1 and y2 == y1 - 1:
        return(0)
    if x2 == x1 + 1 and y2 == y1:
        return(1)
    if x2 == x1 and y2 == y1 + 1:
        return(2)
    if x2 == x1 - 1 and y2 == y1:
        return(3)
    return(-1)

def azimuth_addition(a1, a2):
    return(int((a1 + a2) % 4))

def decode_tank_controls(pos0, a0, direction, a1=-1):
    direction = direction.lower()
    a1 = int(a1)
    if direction == 'f' or direction == 'fwd' or direction == 'forward':
        if np.abs(a0 - a1) == 2: #U-turn
            return(-1)
        pos1 = pos_step(pos0, a0)
    elif direction == 'b' or direction == 'bwd' or direction == 'backward':
        if np.abs(a0 - a1) == 2: #U-turn
            return(-1)
        pos1 = pos_step(pos0, azimuth_addition(a0, 2))
    elif direction == 't' or direction == 'turn':
        pos1 = pos0
    return(pos1, a1)

def human_readable_azimuth(a):
    if a == 0:
        return('up')
    if a == 1:
        return('right')
    if a == 2:
        return('down')
    if a == 3:
        return('left')
    return('jump')

def encode_azimuth(human_readable_a):
    if human_readable_a in ['up', 'u', '^', '0']:
        return(0)
    if human_readable_a in ['right', 'r', '>', '1']:
        return(1)
    if human_readable_a in ['down', 'd', 'v', '2']:
        return(2)
    if human_readable_a in ['left', 'l', '<', '3']:
        return(3)
    return(None)

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   NOTUNDERLINE = '\033[24m'
   LIGHT = '\033[22m' # removes BOLD without resetting color
   DISABLE = '\033[02m'
   END = '\033[0m'

   class bg:
        BLACK = '\033[40m'
        RED = '\033[41m'
        GREEN = '\033[42m'
        ORANGE = '\033[43m'
        BLUE = '\033[44m'
        PURPLE = '\033[45m'
        CYAN = '\033[46m'
        GREY = '\033[47m'
        DEFAULT = '\033[49m'


"""More color options
reset = '\033[0m'
bold = '\033[01m'
disable = '\033[02m'
underline = '\033[04m'
reverse = '\033[07m'
 strikethrough = '\033[09m'
  invisible = '\033[08m'

   class fg:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class bg:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'
"""

def ordered_switch_flips(N, S):
    # Let [bool, bool ... bool] represent the states of N switches.
    # This returns a list of all states with S switches on (True)
    # ordered such that for two states differing only in the position
    # of one on-switch, the state for which the disputed switch is at
    # a lower index will be at a lower index in the returned list.
    if S == 0:
        return([[False] * N])
    if S == N:
        return([[True] * N])
    else:
        res = []
        for last_pos in range(S - 1, N):
            subres = ordered_switch_flips(last_pos, S - 1)
            suffix = [True] + [False] * (N - last_pos - 1)
            for i in range(len(subres)):
                subres[i] += suffix
            res += subres
        return(res)






