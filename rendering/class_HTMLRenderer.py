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
        self.board_window_height = 800

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

    def encode_board_square_id(self, t, x, y):
        return(f"board_square_{t}_{x}_{y}")

    def encode_board_square_class(self, t, x, y):
        if self.render_object.board_static[x][y] == " ":
            return("board_square_empty")
        elif self.render_object.board_static[x][y] == "X":
            return("board_square_wall")
        else:
            return("board_square_unknown")

    def encode_timeslice_id(self, t):
        return(f"timeslice_{t}")

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
        self.deposit_datum("number_of_turns", self.render_object.number_of_turns)

        self.deposit_object("stone_trajectories", self.render_object.stone_trajectories)


        self.deposit_datum("active_turn", self.render_object.active_turn)

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
        self.commit_to_output(f"<div width=\"{self.game_log_width}\" height=\"{self.game_log_height}\" id=\"game_log\">")

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

    def draw_board_square(self, t, x, y):
        # Draws a board square object into the active context
        # ID is position
        # Class is static type
        board_square_object = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"{self.encode_board_square_class(t, x ,y)}\" id=\"{self.encode_board_square_id(t, x, y)}\" onclick=\"board_square_click({t},{x},{y})\" />"
        self.commit_to_output(board_square_object)

    def draw_timeslice(self, t):
        enclosing_group = f"<g id=\"{self.encode_timeslice_id(t)}\" class=\"timeslice_group\">"
        self.commit_to_output(enclosing_group)
        for x in range(self.render_object.x_dim):
            for y in range(self.render_object.y_dim):
                self.draw_board_square(t, x, y)
        self.commit_to_output("</g>")

    # Stone type particulars
    def draw_tank(self, allegiance, stone_ID):
        self.commit_to_output(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{allegiance}_tank\" id=\"{self.encode_stone_ID(stone_ID)}\" transform-origin=\"50px 50px\">")
        self.commit_to_output(f"  <rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"stone_pedestal\" visibility=\"hidden\" />")
        self.commit_to_output(f"  <rect x=\"45\" y=\"10\" width=\"10\" height=\"30\" class=\"{allegiance}_tank_barrel\" />")
        self.commit_to_output(f"  <circle cx=\"50\" cy=\"50\" r=\"20\" class=\"{allegiance}_tank_body\" />")
        self.commit_to_output("</g>")

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
        for t in range(self.render_object.t_dim):
            self.draw_timeslice(t)
        self.draw_stones()
        self.close_board_window()



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

        self.draw_game_log()

        # Close gameside
        self.close_gameside()

        self.finish_output_file()


