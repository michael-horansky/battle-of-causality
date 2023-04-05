
import numpy as np

# Automatic string trimming
def uniform_str(x, l=3):
    x_str = str(x)
    return('0'*(l-len(x_str))+x_str)

# This generates a list [element, element, element...]
def repeated_list(length, element=''):
    result = []
    if type(element) == list:
        for i in range(length):
            result.append(element.copy())
    else:
        for i in range(length):
            result.append(element)
    return(result)

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
    

