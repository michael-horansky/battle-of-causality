# -----------------------------------------------------------------------------
# ---------------------------- class HTMLRenderer -----------------------------
# -----------------------------------------------------------------------------
# This renderer creates a longstring in a HTML format, with interactive
# features managed by JavaScript.
# A hidden form is dynamically altered by user interaction, and can be resolved
# on submission, serverside.


import json

from rendering.class_Renderer import Renderer


class HTMLRenderer(Renderer):

    def __init__(self, render_object):
        super().__init__(render_object)
        self.output = ""
        self.output_path = "resources/renders/"
        self.output_filename = ""

        # ------------------------ Rendering constants ------------------------

        # Document structure
        self.board_control_panel_width = 150
        self.board_control_panel_height = 400

        self.board_window_width = 800
        self.board_window_height = 700

        self.game_log_width = 400
        self.game_log_height = 200

        # Board structure
        self.board_square_base_side_length = 100

    # ------------------- Output file communication methods -------------------

    def create_output_file(self):
        output_file = open(self.output_path + self.output_filename + ".html", "w")
        output_file.write("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Such and such game</title>\n    <link rel=\"stylesheet\" href=\"boc_ingame.css\">\n</head>\n<body onkeydown=\"parse_keydown_event(event)\">\n")
        output_file.close()

    def finish_output_file(self):
        output_file = open(self.output_path + self.output_filename + ".html", "a")
        output_file.write("  <script src=\"boc_ingame.js\"></script>\n</body>\n</html>")
        output_file.close()

    def commit_to_output(self, html_object):
        if isinstance(html_object, str):
            output_file = open(self.output_path + self.output_filename + ".html", "a")
            output_file.write(html_object + "\n")
            output_file.close()
        else:
            for html_object_part in html_object:
                self.commit_to_output(html_object_part)

    # ------------------------ Label mangling methods -------------------------

    def encode_board_square_id(self, x, y):
        return(f"board_square_{x}_{y}")

    def encode_board_square_class(self, x, y):
        # returns a tuple (class_name, z_index)
        if self.render_object.board_static[x][y] == " ":
            return("board_square_empty", 0)
        elif self.render_object.board_static[x][y] == "X":
            return("board_square_wall", 3)
        else:
            return("board_square_unknown", 0)

    def encode_used_time_jump_marker_id(self, x, y):
        return(f"used_time_jump_marker_{x}_{y}")

    def encode_unused_time_jump_marker_id(self, x, y):
        return(f"unused_time_jump_marker_{x}_{y}")

    def encode_stone_ID(self, stone_ID):
        return(f"stone_{stone_ID}")

    # ---------------------- Document structure methods -----------------------
    def deposit_datum(self, name, value):
        self.commit_to_output(f"  const {name} = {value};")

    def deposit_list(self, name, value):
        # If there are no dictionaries in the nest, the output of json.dumps is
        # immediately interpretable by javascript
        self.commit_to_output(f"  const {name} = {json.dumps(value)};")

    def deposit_object(self, name, value):
        self.commit_to_output(f"  const {name} = JSON.parse('{json.dumps(value)}');")

    def deposit_contextual_data(self):
        # This method creates a <script> environment which deposits all data
        # which change between games and which are needed by the JavaScript.
        # This means the main script can be global for all the games :)
        self.commit_to_output(f"<script>")
        # ------------------------ General properties -------------------------
        self.deposit_datum("t_dim", self.render_object.t_dim)
        self.deposit_datum("x_dim", self.render_object.x_dim)
        self.deposit_datum("y_dim", self.render_object.y_dim)
        self.deposit_list("factions", self.render_object.factions)
        self.deposit_list("faction_armies", self.render_object.faction_armies)

        self.deposit_object("stone_trajectories", self.render_object.stone_trajectories)
        self.deposit_list("stone_actions", self.render_object.stone_actions)

        self.deposit_object("time_jumps", self.render_object.time_jumps)

        self.deposit_datum("current_turn", self.render_object.current_turn)

        self.commit_to_output("</script>")

    def open_boardside(self):
        # Boardside is the top two thirds of the screen, containing the board control panel, the board window, and the board interaction panel
        self.commit_to_output("<div id=\"boardside\">")

    def close_boardside(self):
        self.commit_to_output("</div>")

    def open_board_window(self):
        enclosing_div = "<div id=\"board_window\">"
        svg_window = f"<svg width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" xmlns=\"http://www.w3.org/2000/svg\" id=\"board_window_svg\">"
        self.commit_to_output([enclosing_div, svg_window])
        self.board_window_definitions()

    def board_window_definitions(self):
        # Declarations after opening the board window <svg> environment
        used_TJI = []
        used_TJI.append("<radialGradient id=\"grad_used_TJI\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJI.append("  <stop offset=\"40%\" stop-color=\"cyan\" />")
        used_TJI.append("  <stop offset=\"100%\" stop-color=\"blue\" />")
        used_TJI.append("</radialGradient>")
        used_TJO = []
        used_TJO.append("<radialGradient id=\"grad_used_TJO\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJO.append("  <stop offset=\"40%\" stop-color=\"orange\" />")
        used_TJO.append("  <stop offset=\"100%\" stop-color=\"coral\" />")
        used_TJO.append("</radialGradient>")
        used_TJ_conflict = []
        used_TJ_conflict.append("<radialGradient id=\"grad_used_conflict\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJ_conflict.append("  <stop offset=\"40%\" stop-color=\"red\" />")
        used_TJ_conflict.append("  <stop offset=\"100%\" stop-color=\"crimson\" />") #try crimson-brown
        used_TJ_conflict.append("</radialGradient>")

        self.commit_to_output([used_TJI, used_TJO, used_TJ_conflict])

    def draw_board_animation_overlay(self):
        animation_overlay = []
        animation_overlay.append(f"<g id=\"board_animation_overlay\" width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" visibility=\"hidden\">")
        animation_overlay.append(f"  <rect id=\"board_animation_overlay_bg\" x=\"0\" y=\"0\" width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" />")
        animation_overlay.append(f"  <text id=\"board_animation_overlay_text\"  x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" >changeme</text>")
        animation_overlay.append("</g>")
        self.commit_to_output(animation_overlay)

    def close_board_window(self):
        svg_window = "</svg>"
        enclosing_div = "</div>"
        self.commit_to_output([svg_window, enclosing_div])

    def open_gameside(self):
        # Gameside is bottom third of the screen, containing the game control panel and the game log
        self.commit_to_output("<div id=\"gameside\">")

    def close_gameside(self):
        self.commit_to_output("</div>")

    def draw_game_log(self):
        self.commit_to_output(f"<div width=\"{self.game_log_width}px\" height=\"{self.game_log_height}px\" id=\"game_log\">")

        self.commit_to_output(f"<p id=\"navigation_label\"></p>")

        self.commit_to_output("</div>")


    # -------------------------- General svg methods --------------------------

    def get_polygon_points(self, point_matrix, offset = [0, 0]):
        # point_matrix = [[x1, y1], [x2, y2]...]
        # offset = [offset x, offset y]
        result_string = " ".join(",".join(str(pos[i] + offset[i]) for i in range(len(pos))) for pos in point_matrix)
        return(result_string)


    # ---------------------- Board control panel methods ----------------------

    def draw_board_control_panel(self):
        # board control panel allows one to traverse timeslices, and toggle camera controls.
        enclosing_div = "<div id=\"board_control_panel\">"
        enclosing_svg = "<svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"board_control_panel_svg\">"
        self.commit_to_output([enclosing_div, enclosing_svg])

        # Next timeslice button
        next_timeslice_button_points = [[0, 20], [80, 20], [80, 0], [130, 50], [80, 100], [80, 80], [0, 80]]
        next_timeslice_button_polygon = f"<polygon points=\"{self.get_polygon_points(next_timeslice_button_points, [10, 0])}\" class=\"board_control_panel_button\" id=\"next_timeslice_button\" onclick=\"show_next_timeslice()\" />"
        next_timeslice_button_text = "<text x=\"16\" y=\"55\" class=\"button_label\" id=\"next_timeslice_button_label\">Next timeslice</text>"

        # Active timeslice button
        active_timeslice_button_object = f"<rect x=\"20\" y=\"120\" width=\"110\" height=\"60\" rx=\"5\" ry=\"5\" class=\"board_control_panel_button\" id=\"active_timeslice_button\" onclick=\"show_active_timeslice()\" />"
        active_timeslice_button_text = "<text x=\"40\" y=\"127\" class=\"button_label\" id=\"active_timeslice_button_label\"><tspan x=\"50\" dy=\"1.2em\">Active</tspan><tspan x=\"40\" dy=\"1.2em\">timeslice</tspan></text>"

        # Previous timeslice button
        prev_timeslice_button_points = [[130, 20], [50, 20], [50, 0], [0, 50], [50, 100], [50, 80], [130, 80]]
        prev_timeslice_button_polygon = f"<polygon points=\"{self.get_polygon_points(prev_timeslice_button_points, [10, 200])}\" class=\"board_control_panel_button\" id=\"prev_timeslice_button\" onclick=\"show_prev_timeslice()\" />"
        prev_timeslice_button_text = "<text x=27 y=255 class=\"button_label\" id=\"prev_timeslice_button_label\">Prev timeslice</text>"

        self.commit_to_output([next_timeslice_button_polygon, next_timeslice_button_text, active_timeslice_button_object, active_timeslice_button_text, prev_timeslice_button_polygon, prev_timeslice_button_text])

        self.commit_to_output("</svg>\n</div>")


    # ------------------------- Static board methods --------------------------

    def create_board_layer_structure(self, number_of_layers):
        self.board_layer_structure = []
        for n in range(number_of_layers):
            self.board_layer_structure.append([f"<g class=\"board_layer\" id=\"board_layer_{n}\">"])

    def commit_board_layer_structure(self):
        for n in range(len(self.board_layer_structure)):
            self.board_layer_structure[n].append([f"</g>"])
        self.commit_to_output(self.board_layer_structure)

    def draw_board_square(self, x, y):
        # Draws a board square object into the active context
        # ID is position
        # Class is static type
        class_name, z_index = self.encode_board_square_class(x, y)
        board_square_object = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"{class_name}\" id=\"{self.encode_board_square_id(x, y)}\" onclick=\"board_square_click({x},{y})\" />"
        self.board_layer_structure[z_index].append(board_square_object)

        # Draws time jump marker into z-index = 1, with
        # For each square, there is one marker for used and one marker for unused time jumps, and its color depends on whether a TJO, a TJI, or both are present
        # For efficiency, we omit squares whose main markers are placed above the time jump z index
        if z_index <= 1:
            used_time_jump_marker = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"used_time_jump_marker\" id=\"{self.encode_used_time_jump_marker_id(x, y)}\" visibility=\"hidden\" />"
            unused_time_jump_marker_points = [[0, 0], [100, 0], [100, 100], [0, 100], [0, 20], [20, 20], [20, 80], [80, 80], [80, 20], [0, 20]]
            unused_time_jump_marker = f"  <polygon class=\"unused_time_jump_marker\" id=\"{self.encode_unused_time_jump_marker_id(x, y)}\" points=\"{self.get_polygon_points(unused_time_jump_marker_points, [x * self.board_square_base_side_length, y * self.board_square_base_side_length])}\" visibility=\"hidden\" />"
            self.board_layer_structure[1] += [used_time_jump_marker, unused_time_jump_marker]


    def draw_board_squares(self):
        #enclosing_group = f"<g id=\"static_board_squares\">"
        #self.commit_to_output(enclosing_group)
        for x in range(self.render_object.x_dim):
            for y in range(self.render_object.y_dim):
                self.draw_board_square(x, y)
        #self.commit_to_output("</g>")

    # Stone type particulars
    def draw_tank(self, allegiance, stone_ID):
        tank_object = []
        tank_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{allegiance}_tank\" id=\"{self.encode_stone_ID(stone_ID)}\" transform-origin=\"50px 50px\">")
        tank_object.append(f"  <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{allegiance}_tank_animation_effects\" id=\"{self.encode_stone_ID(stone_ID)}_animation_effects\" transform-origin=\"50px 50px\">")
        tank_object.append(f"    <rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"stone_pedestal\" visibility=\"hidden\" />")
        tank_object.append(f"    <rect x=\"45\" y=\"10\" width=\"10\" height=\"30\" class=\"{allegiance}_tank_barrel\" />")
        tank_object.append(f"    <circle cx=\"50\" cy=\"50\" r=\"20\" class=\"{allegiance}_tank_body\" />")
        tank_object.append("  </g>")
        tank_object.append("</g>")
        self.board_layer_structure[4].append(tank_object)

    def draw_stones(self):
        # These are drawn on the x=0,y=0 square with display:none, and will be
        # moved around by JavaScript using the 'transform' attrib1ute.
        # First, we prepare the neutral stones
        for neutral_stone_ID in self.render_object.faction_armies["GM"]:
            pass
        for faction in self.render_object.factions:
            for faction_stone_ID in self.render_object.faction_armies[faction]:
                self.draw_tank(faction, faction_stone_ID)

    def draw_board(self):
        self.open_board_window()
        self.create_board_layer_structure(5) # every element is first added to this, where index = z-index
        self.draw_board_squares()
        self.draw_stones()
        self.commit_board_layer_structure()
        self.draw_board_animation_overlay()
        self.close_board_window()



    # ---------------------- Game control panel methods -----------------------

    def draw_game_control_panel(self):
        # game control panel allows one to traverse rounds, as well as change the game status (resign, offer draw, submit commands, request paradox viewing...).
        enclosing_div = "<div id=\"game_control_panel\">"
        enclosing_svg = "<svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"board_control_panel_svg\">"
        self.commit_to_output([enclosing_div, enclosing_svg])

        # Previous round button
        prev_round_button_points = [[130, 20], [50, 20], [50, 0], [0, 50], [50, 100], [50, 80], [130, 80]]
        prev_round_button_polygon = f"<polygon points=\"{self.get_polygon_points(prev_round_button_points, [10, 0])}\" class=\"game_control_panel_button\" id=\"prev_round_button\" onclick=\"show_prev_round()\" />"
        prev_round_button_text = "<text x=40 y=55 class=\"button_label\" id=\"prev_round_button_label\">Prev round</text>"

        # Active round button
        active_round_button_object = f"<rect x=\"150\" y=\"20\" width=\"110\" height=\"60\" rx=\"5\" ry=\"5\" class=\"game_control_panel_button\" id=\"active_round_button\" onclick=\"show_active_round()\" />"
        active_round_button_text = "<text x=\"170\" y=\"27\" class=\"button_label\" id=\"active_round_button_label\"><tspan x=\"182\" dy=\"1.2em\">Active</tspan><tspan x=\"182\" dy=\"1.2em\">round</tspan></text>"

        # Next round button
        next_round_button_points = [[0, 20], [80, 20], [80, 0], [130, 50], [80, 100], [80, 80], [0, 80]]
        next_round_button_polygon = f"<polygon points=\"{self.get_polygon_points(next_round_button_points, [270, 0])}\" class=\"game_control_panel_button\" id=\"next_round_button\" onclick=\"show_next_round()\" />"
        next_round_button_text = "<text x=\"287\" y=\"55\" class=\"button_label\" id=\"next_round_button_label\">Next round</text>"

        self.commit_to_output([prev_round_button_polygon, prev_round_button_text, active_round_button_object, active_round_button_text, next_round_button_polygon, next_round_button_text])

        self.commit_to_output("</svg>\n</div>")


    # ---------------------------- Global methods -----------------------------

    def render_game(self, output_filename):
        self.output_filename = output_filename
        self.create_output_file()

        self.deposit_contextual_data()

        # Initialize boardside
        self.open_boardside()

        # Draw the board control panel
        self.draw_board_control_panel()

        # Draw the static board as a set of timeslices
        self.draw_board()

        # Close boardside
        self.close_boardside()

        # Open gameside
        self.open_gameside()

        self.draw_game_control_panel()
        self.draw_game_log()

        # Close gameside
        self.close_gameside()

        self.finish_output_file()


