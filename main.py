import sys
import os
import json

# -----------------------------------------------------------------------------
# ---------------------------- Data flow paradigm -----------------------------
# -----------------------------------------------------------------------------
# The game logic is self contained and portable regardless of the renderer.
# An instance of Gamemaster is created, which outputs structured arrays which
# describe the output to be rendered. This "abstract output" is eaten by an
# instance of any renderer class, which then formats the output into a specific
# context.


# We add the parent folder to PYTHONPATH, ensuring sane import paths for all subfolders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_logic.class_Gamemaster import Gamemaster

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

ruleset_rep = {
        "paradox_action" : "permanent_removal",
        "end_without_win" : "draw",
        "scenario_priority" : "conserve_effects_stones_hc"
    }

lol = Gamemaster(display_logs = True)


if cur_client_player == "ng":
    if len(sys.argv) >= 3:
        ng_board_number = int(sys.argv[2])
    else:
        ng_board_number = 2
    lol.load_board(ng_board_number)
    lol.ruleset = ruleset_rep # TODO make this load well
    lol.standard_game_loop()
elif cur_client_player in ["A", "B"]:
    full_static, full_dynamic = load_full_data_from_file()
    lol.load_from_database(full_static, full_dynamic, ruleset_rep)
    lol.open_game(cur_client_player)
else:
    print("Client argument not recognized. Aborting...")
    quit()

if lol.outcome is not None:
    outcome_list = lol.outcome.split(";")
    if outcome_list[0] == "draw":
        print("Client: setting outcome to draw...")
    if outcome_list[0] == "win":
        print(f"Client: setting outcome to win by player {outcome_list[1]}...")


full_static, full_dynamic = lol.dump_to_database()
save_full_data_to_file(full_static, full_dynamic)

#print("Full static:", full_static)
#print("Full dynamic:", full_dynamic)
#print("New dynamic:", lol.dump_changes())

