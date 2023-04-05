

from gamemaster_class import *

gm = gamemaster(1)

gm.standard_game_loop()

"""gm.reset_board()
print(gm.history)
gm.print_board_horizontally()
#gm.change_stone_position(0, (1, 3), (1, 4), 2)
gm.execute_moves(1)
gm.add_spatial_move(0, (4, 3), (4, 2), 0)
gm.execute_moves(2)
gm.add_spatial_move(1, (4, 2), (4, 1), 0, 'B')
gm.execute_moves(3)
gm.add_spatial_move(2, (4, 1), (3, 1), 1)
gm.execute_moves(4)
gm.add_spatial_move(1, (2, 3), (2, 4), 1, 'A')
gm.execute_moves(5)

gm.print_board_horizontally()
gm.execute_moves()
gm.print_board_horizontally()
print([move for move in gm.moves])"""

