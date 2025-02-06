import sys
import json

from class_Gamemaster import Gamemaster

gamefile_name = "resources/games/saving_test"

if len(sys.argv) >= 2:
    cur_client_player = sys.argv[1]
else:
    print("Please pass the client's faction as an argument (\"python3 test_client.py A/B\")")

def save_full_data_to_file(static_data, dynamic_data):
    all_data = {"static_data" : static_data, "dynamic_data" : dynamic_data}
    savefile = open(gamefile_name + ".json", "w")
    json.dump(all_data, savefile, indent=4)
    savefile.close()

def load_full_data_from_file():
    savefile = open(gamefile_name + ".json", "r")
    all_data = json.load(savefile)
    savefile.close()
    return(all_data["static_data"], all_data["dynamic_data"])

lol = Gamemaster(display_logs = True)


"""lol.load_board(1)
lol.standard_game_loop()

full_static, full_dynamic = lol.dump_to_database()

save_full_data_to_file(full_static, full_dynamic)"""

full_static, full_dynamic = load_full_data_from_file()

lol.load_from_database(full_static, full_dynamic)
print("activity maps:", lol.round_canonization)
print("TJI ID buffer:", lol.tji_ID_buffer)


lol.open_game(cur_client_player)

full_static, full_dynamic = lol.dump_to_database()
save_full_data_to_file(full_static, full_dynamic)
#print("Full static:", full_static)
#print("Full dynamic:", full_dynamic)
#print("New dynamic:", lol.dump_changes())

