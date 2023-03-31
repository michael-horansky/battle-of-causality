

from gamemaster_class import *

gm = gamemaster(1)
gm.print_board_horizontally()
gm.change_stone_position(0, (1, 3), (1, 4), 2)
gm.move_stone(0, (4, 3), (4, 2), 0)
gm.move_stone(1, (4, 2), (4, 1), 0)
gm.move_stone(2, (4, 1), (4, 0), 1)
gm.print_board_horizontally()



