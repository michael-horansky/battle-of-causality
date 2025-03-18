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

        self.board_square_empty_color = "#E5E5FF"
        self.unused_TJ_clip_circle_radius = 0.45

        # Board structure
        self.board_square_base_side_length = 100

    # ------------------- Output file communication methods -------------------

    def create_output_file(self):
        output_file = open(self.output_path + self.output_filename + ".html", "w")
        output_file.write("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Battle of Causality: interactive client</title>\n    <link rel=\"stylesheet\" href=\"boc_ingame.css\">\n</head>\n<body onkeydown=\"parse_keydown_event(event)\" onkeyup=\"parse_keyup_event(event)\">\n")
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

    # ---------------------------- Data depositing ----------------------------

    def deposit_datum(self, name, value):
        if isinstance(value, bool):
            if value:
                self.commit_to_output(f"  const {name} = true;")
            else:
                self.commit_to_output(f"  const {name} = false;")
        else:
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
        self.deposit_list("board_static", self.render_object.board_static)
        self.deposit_datum("t_dim", self.render_object.t_dim)
        self.deposit_datum("x_dim", self.render_object.x_dim)
        self.deposit_datum("y_dim", self.render_object.y_dim)
        self.deposit_list("factions", self.render_object.factions)
        self.deposit_list("faction_armies", self.render_object.faction_armies)
        self.deposit_object("stone_properties", self.render_object.stone_properties)

        # Command properties
        self.deposit_datum("did_player_finish_turn", self.render_object.did_player_finish_turn)
        self.deposit_list("stones_to_be_commanded", self.render_object.stones_to_be_commanded)
        self.deposit_object("available_commands", self.render_object.available_commands)

        # ----------------------- Roundwise properties ------------------------
        self.deposit_object("stone_trajectories", self.render_object.stone_trajectories)
        self.deposit_object("stone_endpoints", self.render_object.stone_endpoints)
        self.deposit_list("stone_actions", self.render_object.stone_actions)

        #self.deposit_object("reverse_causality_flags", self.render_object.reverse_causality_flags)
        self.deposit_object("reverse_causality_flag_properties", self.render_object.reverse_causality_flag_properties)
        self.deposit_list("effects", self.render_object.effects)
        self.deposit_list("causes", self.render_object.causes)
        self.deposit_list("activated_buffered_causes", self.render_object.activated_buffered_causes)
        self.deposit_object("scenarios", self.render_object.scenarios)
        self.deposit_object("time_jumps", self.render_object.time_jumps)

        self.deposit_datum("current_turn", self.render_object.current_turn)

        self.commit_to_output("</script>")

    # -------------------------------------------------------------------------
    # ---------------------- Document structure methods -----------------------
    # -------------------------------------------------------------------------

    def open_boardside(self):
        # Boardside is the top two thirds of the screen, containing the board control panel, the board window, and the board interaction panel
        self.commit_to_output("<div id=\"boardside\">")

    def close_boardside(self):
        self.commit_to_output("</div>")

    def open_board_window(self):
        enclosing_div = "<div id=\"board_window\">"
        svg_window = f"<svg width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" xmlns=\"http://www.w3.org/2000/svg\" id=\"board_window_svg\">"
        background_rectangle = f"<rect x=\"0\" y =\"0\" width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" id=\"board_window_background\" />"
        self.commit_to_output([enclosing_div, svg_window, background_rectangle])
        self.board_window_definitions()

    def close_board_window(self):
        svg_window = "</svg>"
        enclosing_div = "</div>"
        self.commit_to_output([svg_window, enclosing_div])

    def open_inspectors(self):
        self.commit_to_output("<div id=\"inspectors\">")

    def close_inspectors(self):
        self.commit_to_output("</div>")

    def open_gameside(self):
        # Gameside is bottom third of the screen, containing the game control panel and the game log
        self.commit_to_output("<div id=\"gameside\">")

    def close_gameside(self):
        self.commit_to_output("</div>")


    # -------------------------- General svg methods --------------------------

    def get_polygon_points(self, point_matrix, offset = [0, 0], scale = 1):
        # point_matrix = [[x1, y1], [x2, y2]...]
        # offset = [offset x, offset y]
        result_string = " ".join(",".join(str(pos[i] * scale + offset[i]) for i in range(len(pos))) for pos in point_matrix)
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


    # ------------------------- Board window methods --------------------------

    def board_window_definitions(self):
        # Declarations after opening the board window <svg> environment

        self.commit_to_output("<defs>")

        # TJ marker gradients
        used_TJI = []
        used_TJI.append("  <radialGradient id=\"grad_used_TJI\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJI.append("    <stop offset=\"40%\" stop-color=\"cyan\" />")
        used_TJI.append("    <stop offset=\"100%\" stop-color=\"blue\" />")
        used_TJI.append("  </radialGradient>")
        used_TJO = []
        used_TJO.append("  <radialGradient id=\"grad_used_TJO\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJO.append("    <stop offset=\"40%\" stop-color=\"orange\" />")
        used_TJO.append("    <stop offset=\"100%\" stop-color=\"coral\" />")
        used_TJO.append("  </radialGradient>")
        used_TJ_conflict = []
        used_TJ_conflict.append("  <radialGradient id=\"grad_used_conflict\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJ_conflict.append("    <stop offset=\"40%\" stop-color=\"red\" />")
        used_TJ_conflict.append("    <stop offset=\"100%\" stop-color=\"crimson\" />") #try crimson-brown
        used_TJ_conflict.append("  </radialGradient>")
        unused_TJI = []
        unused_TJI.append("  <radialGradient id=\"grad_unused_TJI\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        unused_TJI.append("    <stop offset=\"71%\" stop-color=\"cyan\" />")
        unused_TJI.append("    <stop offset=\"100%\" stop-color=\"blue\" />")
        unused_TJI.append("  </radialGradient>")
        unused_TJO = []
        unused_TJO.append("  <radialGradient id=\"grad_unused_TJO\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        unused_TJO.append("    <stop offset=\"71%\" stop-color=\"orange\" />")
        unused_TJO.append("    <stop offset=\"100%\" stop-color=\"coral\" />")
        unused_TJO.append("  </radialGradient>")
        unused_TJ_conflict = []
        unused_TJ_conflict.append("  <radialGradient id=\"grad_unused_conflict\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        unused_TJ_conflict.append("    <stop offset=\"71%\" stop-color=\"red\" />")
        unused_TJ_conflict.append("    <stop offset=\"100%\" stop-color=\"crimson\" />") #try crimson-brown
        unused_TJ_conflict.append("  </radialGradient>")
        self.commit_to_output([used_TJI, used_TJO, used_TJ_conflict, unused_TJI, unused_TJO, unused_TJ_conflict])

        # unused TJ clip-path
        unused_TJ_clip_path = []
        unused_TJ_clip_path.append("  <clipPath id=\"unused_TJ_clip_path\" clipPathUnits=\"objectBoundingBox\" >")
        unused_TJ_clip_path.append(f"    <path d=\"M0,0 L1,0 L1,1 L0,1 L0,0 M{0.5-self.unused_TJ_clip_circle_radius},0.5 A{self.unused_TJ_clip_circle_radius},{self.unused_TJ_clip_circle_radius}, 180, 1, 0, {0.5+self.unused_TJ_clip_circle_radius}, 0.5 A{self.unused_TJ_clip_circle_radius},{self.unused_TJ_clip_circle_radius}, 180, 1, 0, {0.5-self.unused_TJ_clip_circle_radius}, 0.5 Z\"/>")
        unused_TJ_clip_path.append("  </clipPath>")
        self.commit_to_output(unused_TJ_clip_path)

        # drop shadow for highlighting elements
        drop_shadow_filter = []
        drop_shadow_filter.append("<filter id=\"spotlight\">")
        drop_shadow_filter.append("  <feDropShadow dx=\"0\" dy=\"0\" stdDeviation=\"15\" flood-color=\"#ffe100\" flood-opacity=\"1\"/>")
        drop_shadow_filter.append("  <feDropShadow dx=\"0\" dy=\"0\" stdDeviation=\"15\" flood-color=\"#ffe100\" flood-opacity=\"1\"/>")
        drop_shadow_filter.append("</filter>")
        self.commit_to_output(drop_shadow_filter)

        self.commit_to_output("</defs>")

    def open_board_window_camera_scope(self):
        self.commit_to_output(f"<g id=\"camera_subject\" transform-origin=\"{self.render_object.x_dim * self.board_square_base_side_length / 2}px {self.render_object.y_dim * self.board_square_base_side_length / 2}px\">")

    def close_board_window_camera_scope(self):
        self.commit_to_output("</g>")

    def draw_selection_mode_highlights(self):
        # Highlights
        selection_mode_highlights = []
        selection_mode_highlights.append(f"<g id=\"selection_mode_highlights\" width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" visibility=\"hidden\">")
        for x in range(self.render_object.x_dim):
            for y in range(self.render_object.y_dim):
                selection_mode_highlights.append(f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"selection_mode_highlight\" id=\"selection_mode_highlight_{x}_{y}\" />")
        selection_mode_highlights.append(f"</g>")
        self.commit_to_output(selection_mode_highlights)

    def draw_selection_mode_dummies(self):
        # Dummy
        # We draw one dummy of each type
        for allegiance in ["A", "B"]:
            tank_object = []
            tank_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"selection_mode_dummy\" id=\"{allegiance}_tank_dummy\" transform-origin=\"50px 50px\" display=\"none\">")
            tank_object.append(f"  <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"selection_mode_dummy_animation_effects\" id=\"{allegiance}_tank_dummy_animation_effects\" transform-origin=\"50px 50px\">")
            tank_object.append(f"    <rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"stone_pedestal\" visibility=\"hidden\" />")
            tank_object.append(f"    <rect x=\"45\" y=\"10\" width=\"10\" height=\"30\" class=\"{allegiance}_tank_barrel\" />")
            tank_object.append(f"    <circle cx=\"50\" cy=\"50\" r=\"20\" class=\"{allegiance}_tank_body\" />")
            tank_object.append("  </g>")
            tank_object.append("</g>")
            self.commit_to_output(tank_object)

    def draw_selection_mode_azimuth_indicators(self):
        # Azimuth indicators
        triangle_width = 100
        triangle_height = 30
        triangle_offset = 0.1
        azimuth_indicator_points = [
                [[0, -triangle_height], [triangle_width / 2, 0], [-triangle_width / 2, 0]],
                [[triangle_height, 0], [0, triangle_width / 2], [0, -triangle_width / 2]],
                [[0, triangle_height], [triangle_width / 2, 0], [-triangle_width / 2, 0]],
                [[-triangle_height, 0], [0, triangle_width / 2], [0, -triangle_width / 2]]
            ]
        azimuth_indicators = []
        for azimuth in range(4):
            if azimuth == 0:
                offset_x = self.board_window_width / 2
                offset_y = self.board_window_height * triangle_offset
            elif azimuth == 1:
                offset_x = self.board_window_width * (1 - triangle_offset)
                offset_y = self.board_window_height / 2
            elif azimuth == 2:
                offset_x = self.board_window_width / 2
                offset_y = self.board_window_height * (1 - triangle_offset)
            elif azimuth == 3:
                offset_x = self.board_window_width * triangle_offset
                offset_y = self.board_window_height / 2
            azimuth_indicators.append(f"  <polygon points=\"{self.get_polygon_points(azimuth_indicator_points[azimuth], [offset_x, offset_y])}\" class=\"azimuth_indicator\" id=\"azimuth_indicator_{azimuth}\" onclick=\"inspector.select_azimuth({azimuth})\" display=\"none\"/>")
        self.commit_to_output(azimuth_indicators)


    def draw_board_animation_overlay(self):
        animation_overlay = []
        animation_overlay.append(f"<g id=\"board_animation_overlay\" width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" visibility=\"hidden\">")
        animation_overlay.append(f"  <rect id=\"board_animation_overlay_bg\" x=\"0\" y=\"0\" width=\"{self.board_window_width}\" height=\"{self.board_window_height}\" />")
        animation_overlay.append(f"  <text id=\"board_animation_overlay_text\"  x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" >changeme</text>")
        animation_overlay.append("</g>")
        self.commit_to_output(animation_overlay)

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
        board_square_object = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"{class_name}\" id=\"{self.encode_board_square_id(x, y)}\" onclick=\"inspector.board_square_click({x},{y})\" />"
        self.board_layer_structure[z_index].append(board_square_object)

        # Draws time jump marker into z-index = 1, with
        # For each square, there is one marker for used and one marker for unused time jumps, and its color depends on whether a TJO, a TJI, or both are present
        # For efficiency, we omit squares whose main markers are placed above the time jump z index
        if z_index <= 1:
            used_time_jump_marker = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"used_time_jump_marker\" id=\"{self.encode_used_time_jump_marker_id(x, y)}\" visibility=\"hidden\" />"
            #unused_time_jump_marker_points = [[0, 0], [100, 0], [100, 100], [0, 100], [0, 20], [20, 20], [20, 80], [80, 80], [80, 20], [0, 20]]
            #unused_time_jump_marker = f"  <polygon class=\"unused_time_jump_marker\" id=\"{self.encode_unused_time_jump_marker_id(x, y)}\" points=\"{self.get_polygon_points(unused_time_jump_marker_points, [x * self.board_square_base_side_length, y * self.board_square_base_side_length])}\" visibility=\"hidden\" />"
            unused_time_jump_marker = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"unused_time_jump_marker\" id=\"{self.encode_unused_time_jump_marker_id(x, y)}\" visibility=\"hidden\" clip-path=\"url(#unused_TJ_clip_path)\" />"
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

    def draw_square_highlighter(self):
        self.board_layer_structure[3].append(f"<polyline id=\"square_highlighter\" points=\"{self.get_polygon_points([[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]], [0, 0])}\" display=\"none\"/>")

    def draw_board(self):
        self.open_board_window()
        self.open_board_window_camera_scope()
        self.create_board_layer_structure(5) # every element is first added to this, where index = z-index
        self.draw_board_squares()
        self.draw_stones()
        self.draw_square_highlighter()
        self.commit_board_layer_structure()
        self.draw_selection_mode_highlights()
        self.draw_selection_mode_dummies()
        self.close_board_window_camera_scope()
        self.draw_selection_mode_azimuth_indicators()
        self.draw_board_animation_overlay()
        self.close_board_window()

    # --------------------------- Inspector methods ---------------------------

    def draw_inspector_table(self, which_inspector, table_dict):
        # table_dict["js_value_key"] = "human-readable label"
        self.commit_to_output(f"<table id=\"{which_inspector}_info_table\" class=\"inspector_table\">")
        for table_key, table_label in table_dict.items():
            table_element = []
            table_element.append(f"<tr id=\"{which_inspector}_info_{table_key}_container\" class=\"inspector_table_container\">")
            table_element.append(f"  <td id=\"{which_inspector}_info_{table_key}_label\" class=\"{which_inspector}_inspector_table_label\">{table_label}</td>")
            table_element.append(f"  <td id=\"{which_inspector}_info_{table_key}\" class=\"inspector_table_value\"></td>")
            table_element.append(f"</tr>")
            self.commit_to_output(table_element)
        self.commit_to_output(f"</table>")

    def draw_stone_inspector(self):
        # This inspector is used for:
        #   1. Inspecting stone commands
        #   2. Administering stone commands
        self.commit_to_output("<div id=\"stone_inspector\" class=\"inspector\">")
        self.commit_to_output("  <h1 id=\"stone_inspector_title\" class=\"inspector_title\"></h1>")
        self.commit_to_output("  <div id=\"stone_inspector_header\" class=\"stone_inspector_part\">")
        self.draw_inspector_table("stone", {"allegiance" : "Allegiance", "stone_type" : "Stone type", "startpoint" : "Start-point", "endpoint" : "End-point"})
        stone_inspector_object = []
        stone_inspector_object.append("  </div>")
        stone_inspector_object.append("  <div id=\"stone_inspector_commands\" class=\"stone_inspector_part\">")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"stone_inspector_commands_svg\">")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"stone_inspector_selection_mode_buttons_svg\">")
        stone_inspector_object.append("      <g id=\"abort_selection_button\" display=\"none\">")
        stone_inspector_object.append("        <rect x=\"0\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"abort_selection_button_polygon\" onclick=\"inspector.turn_off_selection_mode()\" />")
        stone_inspector_object.append("        <text x=\"50\" y=\"42\" text-anchor=\"middle\" id=\"abort_selection_button_label\" class=\"button_label\">Abort</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("      <g id=\"submit_selection_button\" display=\"none\">")
        stone_inspector_object.append("        <rect x=\"110\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"submit_selection_button_polygon\" onclick=\"inspector.submit_selection()\" />")
        stone_inspector_object.append("        <text x=\"160\" y=\"42\" text-anchor=\"middle\" class=\"button_label\">Submit</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("  </div>")
        stone_inspector_object.append("</div>")
        self.commit_to_output(stone_inspector_object)

    def draw_tracking_inspector(self):
        self.commit_to_output("<div id=\"tracking_inspector\" class=\"inspector\">")
        #self.commit_to_output("  <p id=\"stone_tracking_label\"></p>")
        self.commit_to_output("  <div id=\"tracking_inspector_header\">")
        self.commit_to_output("    <p id=\"stone_tracking_label\"></p>")
        self.commit_to_output("  </div>")
        self.commit_to_output(f"  <svg width=\"70%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"tracking_inspector_svg\">")


        # Start-point button
        startpoint_button_points = [[130, 20], [50, 20], [50, 0], [0, 50], [50, 100], [50, 80], [130, 80]]
        startpoint_button_polygon = f"<polygon points=\"{self.get_polygon_points(startpoint_button_points, [10, 10], 0.8)}\" class=\"game_control_panel_button\" id=\"tracking_startpoint_button\" onclick=\"tracking_startpoint()\" />"
        startpoint_button_text = "<text x=25 y=55 class=\"button_label\" id=\"tracking_startpoint_button_label\">Start-point</text>"

        # End-point button
        endpoint_button_points = [[0, 20], [80, 20], [80, 0], [130, 50], [80, 100], [80, 80], [0, 80]]
        endpoint_button_polygon = f"<polygon points=\"{self.get_polygon_points(endpoint_button_points, [120, 10], 0.8)}\" class=\"game_control_panel_button\" id=\"tracking_endpoint_button\" onclick=\"tracking_endpoint()\" />"
        endpoint_button_text = "<text x=\"128\" y=\"55\" class=\"button_label\" id=\"tracking_endpoint_button_label\">End-point</text>"

        # Turn off tracking button
        turn_off_tracking_button_object = f"<rect x=\"235\" y=\"26\" width=\"88\" height=\"48\" rx=\"5\" ry=\"5\" class=\"game_control_panel_button\" id=\"turn_off_tracking_button\" onclick=\"cameraman.track_stone(null)\" />"
        turn_off_tracking_button_text = "<text x=\"238\" y=\"27\" class=\"button_label\" id=\"turn_off_tracking_button_label\"><tspan x=\"248\" dy=\"1.2em\">Turn off</tspan><tspan x=\"248\" dy=\"1.2em\">tracking</tspan></text>"

        self.commit_to_output([startpoint_button_polygon, startpoint_button_text, endpoint_button_polygon, endpoint_button_text, turn_off_tracking_button_object, turn_off_tracking_button_text])

        self.commit_to_output("  </svg>")
        self.commit_to_output("</div>")


    def draw_square_inspector(self):
        square_inspector_object = []
        self.commit_to_output("<div id=\"square_inspector\" class=\"inspector\">")
        self.commit_to_output("  <h1 id=\"square_inspector_title\" class=\"inspector_title\"></h1>")
        #square_inspector_object.append("  <p id=\"square_info_used_tp\"></p>")
        #square_inspector_object.append("  <p id=\"square_info_unused_tp\"></p>")
        self.draw_inspector_table("square", {"active_effects" : "Active ante-effects", "activated_causes" : "Activated retro-causes", "inactive_effects" : "Inactive ante-effects", "not_activated_causes" : "Not activated retro-causes"})
        self.commit_to_output("</div>")

    def draw_choice_selector(self):
        # Replaces tracking_inspector in selection mode
        choice_selector = []
        choice_selector.append("<div id=\"choice_selector\" class=\"selector\" style=\"display:none;\">")
        choice_selector.append("  <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"choice_selector_buttons_svg\">")
        choice_selector.append("  </svg>")
        choice_selector.append("</div>")
        self.commit_to_output(choice_selector)

    def draw_swap_effect_selector(self):
        # Replaces tracking_inspector in selection mode
        choice_selector = []
        choice_selector.append("<div id=\"swap_effect_selector\" class=\"selector\" style=\"display:none;\">")
        choice_selector.append("  <table id=\"swap_effect_selector_table\" class=\"selector_table\">")
        choice_selector.append("  </table>")
        choice_selector.append("</div>")
        self.commit_to_output(choice_selector)

    def draw_inspectors(self):
        self.open_inspectors()
        self.draw_stone_inspector()
        self.draw_tracking_inspector()
        self.draw_square_inspector()
        self.draw_choice_selector()
        self.draw_swap_effect_selector()
        self.close_inspectors()

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

    # --------------------------- Game log methods ----------------------------

    def draw_game_log(self):
        self.commit_to_output(f"<div width=\"{self.game_log_width}px\" height=\"{self.game_log_height}px\" id=\"game_log\">")

        self.commit_to_output(f"  <p id=\"navigation_label\"></p>")

        self.commit_to_output("</div>")


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

        # Draw inspectors
        self.draw_inspectors()

        # Close boardside
        self.close_boardside()

        # Open gameside
        self.open_gameside()

        self.draw_game_control_panel()
        self.draw_game_log()

        # Close gameside
        self.close_gameside()

        self.finish_output_file()


