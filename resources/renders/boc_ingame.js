
// ----------------------------------------------------------------------------
// --------------------------- Rendering constants ----------------------------
// ----------------------------------------------------------------------------
const board_window_width = 800;
const board_window_height = 700;

const stone_command_btn_width = 100;
const stone_command_btn_height = 83;
// ----------------------------------------------------------------------------
// --------------------------- HTML DOM management ----------------------------
// ----------------------------------------------------------------------------

function write_to_html(html_object){
    // If html_object is a string, it is printed into the html document
    // If it is an array of strings, all elements are printed into the html document sequentially, flattening the array (levels can be multiple)
    if(typeof html_object === 'string') {
        document.write(html_object);
    } else {
        for (let i = 0; i < html_object.length; i++) {
            write_to_html(html_object[i]);
        }
    }

}

function make_SVG_element(tag, attrs) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs) {
      el.setAttribute(k, attrs[k]);
    }
    return el;
}

function remove_elements_by_class(class_name){
    const elements = document.getElementsByClassName(class_name);
    while(elements.length > 0){
        elements[0].parentNode.removeChild(elements[0]);
    }
}

// ----------------------------------------------------------------------------
// ---------------------------------- Logic -----------------------------------
// ----------------------------------------------------------------------------

function round_from_turn(turn_index) {
    if (turn_index == 0) {
        return [0, -1];
    }
    let current_round_number = Math.floor((turn_index - 1) / t_dim);
    let current_timeslice    = (turn_index - 1) % t_dim;
    return [current_round_number, current_timeslice];
}

function is_flag_at_pos(flag_ID, t, x, y) {
    if (reverse_causality_flag_properties[flag_ID] == undefined) {
        alert(`[Flag ID: ${flag_ID}] properties requested at (${t},${x},${y}) but flag does not exist.`);
    }
    return (reverse_causality_flag_properties[flag_ID]["t"] == t && reverse_causality_flag_properties[flag_ID]["x"] == x && reverse_causality_flag_properties[flag_ID]["y"] == y);
}

function find_stone_at_pos(x, y) {
    for (let faction_i = 0; faction_i < factions.length; faction_i++) {
        for (let stone_i = 0; stone_i < faction_armies[factions[faction_i]].length; stone_i++) {
            if (stone_trajectories[selected_round][visible_timeslice]["canon"][faction_armies[factions[faction_i]][stone_i]] != null) {
                if (arrays_equal(stone_trajectories[selected_round][visible_timeslice]["canon"][faction_armies[factions[faction_i]][stone_i]].slice(0,2), [x, y])) {
                    return faction_armies[factions[faction_i]][stone_i];
                }
            }
        }
    }
    return null;
}

function bound(val, lower_bound, upper_bound) {
    return Math.max(lower_bound, Math.min(val, upper_bound));
}

function cubic_bezier(t, params) {
    // t = 0 => 0
    // t = 1 => 1
    return (t*(t*(t+(1-t)*params[1])+(1-t)*(t*params[1]+(1-t)*params[0]))+(1-t)*(t*(t*params[1]+(1-t)*params[0])+(1-t)*(t*params[0])));
}
function cubic_bezier_boomerang(t, params) {
    // t = 0 => 0
    // t = 1 => 0
    return (1-t)*((1-t)*(t*params[0])+t*((1-t)*params[0]+t*params[1]))+t*((1-t)*((1-t)*params[0]+t*params[1])+t*((1-t)*params[1]));
}

function arrays_equal(arr1, arr2) {
    return arr1.every((value, index) => value == arr2[index]);
}

// Vector algebra
function vec_add(vec1, vec2){
    return vec1.map((e,i) => e + vec2[i]);
}

function vec_sub(vec1, vec2){
    return vec1.map((e,i) => e - vec2[i]);
}

function vec_scale(vec, coef){
    return vec.map((e,i) => e * coef);
}

function vec_round(vec) {
    return vec.map((e,i) => Math.round(e));
}

// Matrix algebra
function mat_add(mat1,mat2){
    return mat1.map((row_vec,row_i) => (row_vec.map((e, col_i) => ([e,mat2[row_i][col_i]].includes(null) ? null : e + mat2[row_i][col_i]  ))));
}

function mat_sub(mat1,mat2){
    return mat1.map((row_vec,row_i) => (row_vec.map((e, col_i) => ([e,mat2[row_i][col_i]].includes(null) ? null : e - mat2[row_i][col_i]))));
}

function mat_scale(mat, coef){
    return mat.map((row_vec,row_i) => (row_vec.map((e, col_i) => (e == null ? null : e * coef))));
}

function mat_round(mat) {
    return mat.map((row_vec,row_i) => (row_vec.map((e, col_i) => (e == null ? null : Math.round(e)))));
}

function animated_scalar_transformation(val_start, val_end, total_frames, frame_key, method="traverse") {
    // val_start, val_end are numbers which denote the parameter to be animated
    // total_frames is the number of frames, frame_key is the current frame id.
    switch (method) {
        case "traverse":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.1, 1]);
        case "boomerang":
            return val_start + (val_end - val_start) * cubic_bezier_boomerang(frame_key / total_frames, [0.2, 2.1]);
        case "linear":
            return val_start + (val_end - val_start) * frame_key / total_frames;
    }
    /*if (method == "traverse") {
        return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.1, 1]);
    }
    if (method == "boomerang") {
        return val_start + (val_end - val_start) * cubic_bezier_boomerang(frame_key / total_frames, [0.2, 2.1]);
    }*/

}

function animated_vector_transformation(vec_start, vec_end, total_frames, frame_key) {
    // vec_start, vec_end are vectors which denote the parameter to be animated
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return vec_add(vec_start, vec_scale(vec_sub(vec_end, vec_start), cubic_bezier(frame_key / total_frames, [0.1, 1])));
}

function animated_matrix_transformation(mat_start, mat_end, total_frames, frame_key) {
    // mat_start, mat_end are matrices encoding the parameters to be animated.
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return mat_add(mat_start, mat_scale(mat_sub(mat_end, mat_start), cubic_bezier(frame_key / total_frames, [0.1, 1])));
}


function inds(obj, inds, to_str = true) {
    // accesses an element of object from a stack of indices, or returns undefined if indices don't exist
    // if to_str, indices are automatically converted to strings
    let obj_stack = [obj];
    if (to_str) {
        for (inds_i = 0; inds_i < inds.length; inds_i++) {
            if (obj_stack[inds_i][inds[inds_i].toString()] == undefined) {
                return undefined;
            }
            obj_stack.push(obj_stack[inds_i][inds[inds_i].toString()]);
        }
    } else {
        for (inds_i = 0; inds_i < inds.length; inds_i++) {
            if (obj_stack[inds_i][inds[inds_i]] == undefined) {
                return undefined;
            }
            obj_stack.push(obj_stack[inds_i][inds[inds_i]]);
        }
    }
    return obj_stack[inds.length];
}

// ----------------------------------------------------------------------------
// ---------------------- Graphical attribute management ----------------------
// ----------------------------------------------------------------------------

function select_timeslice(new_timeslice) {
    selected_timeslice = new_timeslice;
    document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}, selected round ${selected_round}`;
}

function select_round(new_round_n, new_timeslice = null) {
    selected_round = new_round_n;
    if (new_timeslice != null) {
        selected_timeslice = new_timeslice;
    }
    document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}, selected round ${selected_round}`;
}

function show_canon_board_slice(round_n, timeslice){
    visible_round = round_n;
    visible_timeslice = timeslice;
    visible_process = "canon";
    show_stones_at_process(round_n, timeslice, "canon");
    show_time_jumps_at_time(round_n, timeslice);
    if (inspector.selection_mode_enabled) {
        // We take care of the selection choice highlighting
        for (x = 0; x < x_dim; x++) {
            for (y = 0; y < y_dim; y++) {
                document.getElementById(`selection_mode_highlight_${x}_${y}`).style.fill = "grey";
            }
        }
        for (i = 0; i < inspector.selection_mode_options["squares"].length; i++) {
            if (inspector.selection_mode_options["squares"][i]["t"] == visible_timeslice) {
                document.getElementById(`selection_mode_highlight_${inspector.selection_mode_options["squares"][i]["x"]}_${inspector.selection_mode_options["squares"][i]["y"]}`).style.fill = "green";
            }
        }
        // If a choice has been made, we place the selection mode dummy at its appropriate place
        selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
        for (i = 0; i < selection_mode_dummies.length; i++) {
            selection_mode_dummies[i].style.display = "none";
        }
        if (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false) {
            let selected_square = inspector.selection_mode_options["squares"][inspector.selection["square"]];
            document.getElementById(`B_tank_dummy`).style.transform = `translate(${100 * selected_square["x"]}px,${100 * selected_square["y"]}px) rotate(${90 * inspector.selection["azimuth"]}deg)`;
            document.getElementById(`B_tank_dummy`).style.display = "inline";
        }
    }
}

function hide_all_stones(){
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            document.getElementById(`stone_${stone_ID}`).style.display = "none";
        });
    });
}

function show_time_jumps_at_time(round_n, time) {
    for (let x = 0; x < x_dim; x++) {
        for (let y = 0; y < y_dim; y++) {
            let current_used_time_jump_marker = document.getElementById(`used_time_jump_marker_${x}_${y}`);
            let current_unused_time_jump_marker = document.getElementById(`unused_time_jump_marker_${x}_${y}`);
            if (current_used_time_jump_marker != undefined) {
                let used_tj_marker = inds(time_jumps[round_n], [time, x, y, "used"]);
                let unused_tj_marker = inds(time_jumps[round_n], [time, x, y, "unused"]);
                if (used_tj_marker != undefined) {
                    current_used_time_jump_marker.style.fill = `url(#grad_used_${used_tj_marker})`;
                    current_used_time_jump_marker.style.opacity = "1";
                    current_used_time_jump_marker.style.visibility = "visible";
                } else {
                    current_used_time_jump_marker.style.visibility = "hidden";
                }
                if (unused_tj_marker != undefined) {
                    current_unused_time_jump_marker.style.fill = `url(#grad_unused_${unused_tj_marker})`;
                    current_unused_time_jump_marker.style.opacity = "1";
                    current_unused_time_jump_marker.style.visibility = "visible";
                } else {
                    current_unused_time_jump_marker.style.visibility = "hidden";
                }
            }
        }
    }
}

function show_stones_at_process(round_n, time, process_key){
    // NOT animated
    // This resets the animation properties (opacity, scale)
    visible_timeslice = time;
    visible_process = process_key;
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            let stone_state = stone_trajectories[round_n][time][process_key][`${stone_ID}`];
            //alert(`stone ${stone_ID} is in state ${stone_state}`);
            if (stone_state == null) {
                document.getElementById(`stone_${stone_ID}`).style.display = "none";
            } else {
                document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * stone_state[0]}px,${100 * stone_state[1]}px) rotate(${90 * stone_state[2]}deg)`;
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.transform = "";
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.opacity = "1";
                document.getElementById(`stone_${stone_ID}`).style.display = "inline";
            }
        });
    });
}

function hide_stones(local_stone_list) {
    local_stone_list.forEach(function(stone_ID, stone_index){
        document.getElementById(`stone_${stone_ID}`).style.display = "none";
    });
}

function show_stones_at_state(local_stone_list, state_matrix, scale = null, opacity = null){
    // state_matrix[index in local_stone_list] = null or [x, y, azimuth]
    // scale and opacity are global properties and default to 1
    local_stone_list.forEach(function(stone_ID, stone_index){
        let stone_state = state_matrix[stone_index];
        if (stone_state == null) {
            document.getElementById(`stone_${stone_ID}`).style.display = "none";
        } else {
            document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * stone_state[0]}px,${100 * stone_state[1]}px) rotate(${90 * stone_state[2]}deg)`;
            if (scale != null) {
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.transform = `scale(${scale})`;
            }
            if (opacity != null) {
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.opacity = `${opacity}`;
            }
            document.getElementById(`stone_${stone_ID}`).style.display = "inline";
        }
    });
}

function show_class_at_state(class_name, scale = null, opacity = null) {
    let class_elements = document.getElementsByClassName(class_name);
    for (let class_index = 0; class_index < class_elements.length; class_index++) {
        if (scale != null) {
            class_elements[class_index].style.transform = `scale(${scale})`;
        }
        if (opacity != null) {
            class_elements[class_index].style.opacity = `${opacity}`;
        }
        class_elements[class_index].style.display = `inline`;
    }
}

function show_ids_at_state(list_of_ids, scale = null, opacity = null) {
    for (let id_index = 0; id_index < list_of_ids.length; id_index++) {
        cur_element = document.getElementById(list_of_ids[id_index]);
        if (cur_element != undefined) {
            if (scale != null) {
                cur_element.style.transform = `scale(${scale})`;
            }
            if (opacity != null) {
                cur_element.style.opacity = `${opacity}`;
            }
            cur_element.style.display = `inline`;
        }
    }
}

// ----------------------------------------------------------------------------
// ---------------------------- Animation manager -----------------------------
// ----------------------------------------------------------------------------

const animation_manager = new Object();
animation_manager.animation_queue = [];
animation_manager.animation_daemon = null;
animation_manager.temporary_element_classes = [];
animation_manager.is_playing = false;
animation_manager.current_frame_key = 0;
animation_manager.default_total_frames = 40;
animation_manager.default_frame_latency = 5;
animation_manager.dictionary_of_animations = new Object();
animation_manager.reset_animation = function() {
    animation_manager.animation_daemon = null;
    animation_manager.is_playing = false;
    animation_manager.current_frame_key = 0;
    while (animation_manager.temporary_element_classes.length > 0) {
        remove_elements_by_class(animation_manager.temporary_element_classes.shift());
    }
}
animation_manager.add_TAE_class = function(TAE_class_name) {
    if (!(animation_manager.temporary_element_classes.includes(TAE_class_name))) {
        animation_manager.temporary_element_classes.push(TAE_class_name);
    }
}
animation_manager.create_causal_freedom_marker = function(pos_x, pos_y) {
    let new_group = make_SVG_element("g", {
        class : "TAE_causal_freedom_marker",
        id : `causal_freedom_marker_${pos_x}_${pos_y}`,
        x : 0,
        y : 0,
        width : 100,
        height : 100,
        display : "none"
    });
    document.getElementById("board_layer_4").appendChild(new_group);
    question_mark = make_SVG_element("text", {
        x : 30,
        y : 80,
        "font-size" : "5em"
    });
    question_mark.textContent = "?";
    new_group.appendChild(question_mark);
    new_group.style.transform = `translate(${100 * pos_x}px,${100 * pos_y}px)`;
}
animation_manager.create_stone_action_marker = function(stone_action) {
    switch(true) {
        case arrays_equal(stone_action.slice(0,2), ["tank", "attack"]):
            new_group = make_SVG_element("g", {
                class : "TAE_tank_attack",
                id : `TAE_tank_attack_${stone_action[2]}_${stone_action[3]}`,
                x : 0,
                y : 0
            });
            document.getElementById("board_layer_2").appendChild(new_group);
            laser_line = make_SVG_element("line", {
                x1 : 50,
                y1 : 50,
                x2 : 50 + 100*(stone_action[4]-stone_action[2]),
                y2 : 50 + 100*(stone_action[5]-stone_action[3]),
                "stroke" : "red",
                "stroke-width" : 7
            });
            new_group.appendChild(laser_line);
            new_group.style.transform = `translate(${100 * stone_action[2]}px,${100 * stone_action[3]}px)`;
            break;
    }
}
animation_manager.shift_frame_method = function(current_animation) {
    if (animation_manager.current_frame_key == animation_manager.total_frames) {
        clearInterval(animation_manager.animation_daemon);
        // animation cleanup
        animation_manager.dictionary_of_animations[current_animation[0]]["cleanup"](current_animation.slice(1));
        animation_manager.reset_animation();
        animation_manager.play_if_available();
    } else {
        animation_manager.current_frame_key += 1;
        animation_manager.dictionary_of_animations[current_animation[0]]["frame"](current_animation.slice(1));
    }
}
animation_manager.play_if_available = function() {
    if (animation_manager.is_playing == false) {
        if (animation_manager.animation_queue.length > 0) {
            let current_animation = animation_manager.animation_queue.shift();
            if (typeof(current_animation) == 'string') {
                // Magic word
                switch(current_animation) {
                    case "reset_to_canon":
                        visible_process = "canon";
                        show_canon_board_slice(visible_round, visible_timeslice);
                        cameraman.apply_tracking();
                }
                animation_manager.play_if_available();
            } else {
                animation_manager.is_playing = true;
                // prepare contextual animation specifications
                animation_manager.total_frames = animation_manager.dictionary_of_animations[current_animation[0]]["total_frames"];
                animation_manager.frame_latency = animation_manager.dictionary_of_animations[current_animation[0]]["frame_latency"];
                animation_manager.dictionary_of_animations[current_animation[0]]["preparation"](current_animation.slice(1));
                animation_manager.animation_daemon = setInterval(animation_manager.shift_frame_method, animation_manager.frame_latency, current_animation);
            }
        }
    }
}

animation_manager.add_to_queue = function(list_of_animations) {
    // Each animation is a list, where the first element is a key in dictionary_of_animations
    list_of_animations.forEach(function(animation_args, index) {
        if (typeof(animation_args) == 'string') {
            // It's a magic word!
            animation_manager.animation_queue.push(animation_args);
        } else {
            switch(animation_args[0]) {
                case "change_process":
                    if (!(inbetweens[animation_args[1]][animation_args[2]][animation_args[3]]["redundant"])) {
                        animation_manager.animation_queue.push(animation_args);
                    }
                    break;
                default:
                    animation_manager.animation_queue.push(animation_args);
            }
        }
    });
    //animation_manager.animation_queue = animation_manager.animation_queue.concat(list_of_animations);
    animation_manager.play_if_available();
}

animation_manager.clear_queue = function() {
    // clears queue and interrupts current animation
    if (animation_manager.is_playing) {
        clearInterval(animation_manager.animation_daemon);
    }
    animation_manager.reset_animation();
    animation_manager.animation_queue = [];
}

animation_manager.default_preparation = function(animation_args) {

}
animation_manager.default_cleanup = function(animation_args) {

}

animation_manager.add_animation = function(animation_name, animation_object) {
    if (animation_object["frame"] == undefined) {
        alert("Submitted animation object has to posses the 'frame' property!");
        return null;
    }
    animation_manager.dictionary_of_animations[animation_name] = animation_object;
    if (animation_manager.dictionary_of_animations[animation_name]["preparation"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["preparation"] = animation_manager.default_preparation;
    }
    if (animation_manager.dictionary_of_animations[animation_name]["cleanup"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["cleanup"] = animation_manager.default_cleanup;
    }
    if (animation_manager.dictionary_of_animations[animation_name]["total_frames"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["total_frames"] = animation_manager.default_total_frames;
    }
    if (animation_manager.dictionary_of_animations[animation_name]["frame_latency"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["frame_latency"] = animation_manager.default_frame_latency;
    }
}

// --------------------------- shift_frame methods ----------------------------

// change_process
animation_manager.change_process_preparation = function(animation_args) {
    let round_n = animation_args[0];
    let s_time = animation_args[1];
    let s_process = animation_args[2];
    let play_backwards = animation_args[3];
    // Create causal-freedom-signifiers for all stones destroyed when s_process = canon
    if (s_process == "canon") {
        if (inbetweens[round_n][s_time][s_process]["dest_stones"].length > 0) {
            animation_manager.add_TAE_class("TAE_causal_freedom_marker");
            for (let stone_index = 0; stone_index < inbetweens[round_n][s_time][s_process]["dest_stones"].length; stone_index++) {
                animation_manager.create_causal_freedom_marker(inbetweens[round_n][s_time][s_process]["dest_stones_states"][stone_index][0], inbetweens[round_n][s_time][s_process]["dest_stones_states"][stone_index][1]);
            }
        }
    }

    // Create various markers for stone and board actions when s_process = "tagscreens"
    if (s_process == "tagscreens") {
        for (let stone_action_index = 0; stone_action_index < stone_actions[round_n][s_time].length; stone_action_index++) {
            let cur_action = stone_actions[round_n][s_time][stone_action_index];
            animation_manager.add_TAE_class(`TAE_${cur_action[0]}_${cur_action[1]}`);
            animation_manager.create_stone_action_marker(cur_action);
        }
    }

    // Prepare time jump markers
    inbetweens[round_n][s_time][s_process]["new_time_jumps"][0].forEach(function(time_jump_mark, index) {
        time_jump_element = document.getElementById(time_jump_mark);
        if (play_backwards) {
            time_jump_element.style.opacity = "1";
        } else {
            time_jump_element.style.opacity = "0";
        }
        time_jump_element.style.fill = `url(#grad_${inbetweens[round_n][s_time][s_process]["new_time_jumps"][1][index]})`;
        time_jump_element.style.visibility = "visible";
    });
    inbetweens[round_n][s_time][s_process]["old_time_jumps"][0].forEach(function(time_jump_mark, index) {
        time_jump_element = document.getElementById(time_jump_mark);
        if (play_backwards) {
            time_jump_element.style.opacity = "0";
        } else {
            time_jump_element.style.opacity = "1";
        }
        time_jump_element.style.fill = `url(#grad_${inbetweens[round_n][s_time][s_process]["old_time_jumps"][1][index]})`;
        time_jump_element.style.visibility = "visible";
    });

}
animation_manager.change_process_get_frame = function(animation_args) {
    let round_n = animation_args[0];
    let s_time = animation_args[1];
    let s_process = animation_args[2];
    let play_backwards = animation_args[3];
    let contextual_frame_key = (play_backwards ? animation_manager.total_frames - animation_manager.current_frame_key : animation_manager.current_frame_key);
    //alert(animated_matrix_transformation(inbetweens[round_n][start_time][start_process]["cont_stones_states"][0], inbetweens[round_n][start_time][start_process]["cont_stones_states"][1], total_frames, cur_frame_key));
    show_stones_at_state(inbetweens[round_n][s_time][s_process]["cont_stones"], animated_matrix_transformation(inbetweens[round_n][s_time][s_process]["cont_stones_states"][0], inbetweens[round_n][s_time][s_process]["cont_stones_states"][1], animation_manager.total_frames, contextual_frame_key));
    // Dest stones: if s_process = "canon", the stones will not be placed on "flags", which means they weren't destroyed, but are causally free.
    if (s_process != "canon") {
        show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], animated_scalar_transformation(1, 2, animation_manager.total_frames, contextual_frame_key), animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
    } else {
        show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
        show_class_at_state("TAE_causal_freedom_marker", null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key, "boomerang"));
    }
    show_stones_at_state(inbetweens[round_n][s_time][s_process]["new_stones"], inbetweens[round_n][s_time][s_process]["new_stones_states"], 1, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key));
    show_ids_at_state(inbetweens[round_n][s_time][s_process]["new_time_jumps"][0], null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key));
    show_ids_at_state(inbetweens[round_n][s_time][s_process]["old_time_jumps"][0], null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
    // If tracking, we find the tracking stone's state
    if (cameraman.tracking_stone != null) {
        if (inbetweens[round_n][s_time][s_process]["new_stones"].includes(cameraman.tracking_stone)) {
            cameraman.apply_tracking(inbetweens[round_n][s_time][s_process]["new_stones_states"][inbetweens[round_n][s_time][s_process]["new_stones"].indexOf(cameraman.tracking_stone)]);
            cameraman.used_by_an_animation = true;
        } else if (inbetweens[round_n][s_time][s_process]["dest_stones"].includes(cameraman.tracking_stone)) {
            cameraman.apply_tracking(inbetweens[round_n][s_time][s_process]["dest_stones_states"][inbetweens[round_n][s_time][s_process]["dest_stones"].indexOf(cameraman.tracking_stone)]);
            cameraman.used_by_an_animation = true;
        } else if (inbetweens[round_n][s_time][s_process]["cont_stones"].includes(cameraman.tracking_stone)) {
            let tracking_stone_index = inbetweens[round_n][s_time][s_process]["cont_stones"].indexOf(cameraman.tracking_stone);
            cameraman.apply_tracking(animated_vector_transformation(inbetweens[round_n][s_time][s_process]["cont_stones_states"][0][tracking_stone_index], inbetweens[round_n][s_time][s_process]["cont_stones_states"][1][tracking_stone_index], animation_manager.total_frames, contextual_frame_key));
            cameraman.used_by_an_animation = true;
        }
    }
}
animation_manager.change_process_cleanup = function(animation_args) {
    let round_n = animation_args[0];
    let s_time = animation_args[1];
    let s_process = animation_args[2];
    let play_backwards = animation_args[3];
    if (play_backwards) {
        show_stones_at_process(round_n, s_time, s_process);
        show_time_jumps_at_time(round_n, s_time);
    } else {
        if (s_process == "canon") {
            show_stones_at_process(round_n, s_time + 1, process_keys[0]);
            show_time_jumps_at_time(round_n, s_time + 1);
        } else {
            show_stones_at_process(round_n, s_time, process_keys[process_keys.indexOf(s_process) + 1]);
            show_time_jumps_at_time(round_n, s_time);
        }
    }
    // Hide time jump markers
    if (play_backwards) {
        inbetweens[round_n][s_time][s_process]["new_time_jumps"][0].forEach(function(new_time_jump_id, index) {
            document.getElementById(new_time_jump_id).style.visibility = "hidden";
        });
    } else {
        inbetweens[round_n][s_time][s_process]["old_time_jumps"][0].forEach(function(new_time_jump_id, index) {
            document.getElementById(new_time_jump_id).style.visibility = "hidden";
        });
    }
    // Update camera
    cameraman.used_by_an_animation = false;
    // Only if the tracking stone changed position or recently appeared, we reset the highlight
    cameraman.apply_tracking();
}

// change_round
animation_manager.change_round_preparation = function(animation_args) {
    let animation_overlay_msg = animation_args[2];
    let transition_direction = animation_args[3];
    // disable timeslice navigation
    set_timeslice_navigation(false);
    // Show the animation overlay
    document.getElementById("board_animation_overlay_text").textContent = animation_overlay_msg;
    document.getElementById("board_animation_overlay_bg").style.fill = "rgb(200, 200, 200)";
    switch (transition_direction) {
        case "down":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${- board_window_height}px)`;
            break;
        case "left":
            document.getElementById("board_animation_overlay").style.transform = `translate(${board_window_width}px,0px)`;
            break;
        case "up":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${board_window_height}px)`;
            break;
        case "right":
            document.getElementById("board_animation_overlay").style.transform = `translate(${-board_window_width}px,0px)`;
            break;
    }
    document.getElementById("board_animation_overlay").style.visibility = "visible";
}
animation_manager.change_round_get_frame = function(animation_args) {
    let new_round = animation_args[0];
    let new_timeslice = animation_args[1];
    let transition_direction = animation_args[3];

    // Change the style of animation overlay
    //document.getElementById("board_animation_overlay").style.opacity = animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, animation_manager.current_frame_key, "boomerang");
    switch (transition_direction) {
        case "down":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${animated_scalar_transformation(- board_window_height, board_window_height, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px)`;
            break;
        case "left":
            document.getElementById("board_animation_overlay").style.transform = `translate(${animated_scalar_transformation(board_window_width, -board_window_width, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px,0px)`;
            break;
        case "up":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${animated_scalar_transformation(board_window_height, -board_window_height, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px)`;
            break;
        case "right":
            document.getElementById("board_animation_overlay").style.transform = `translate(${animated_scalar_transformation(- board_window_width, board_window_width, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px,0px)`;
            break;
    }

    // If we're halfway done, show the new round
    if (animation_manager.current_frame_key / animation_manager.total_frames > 0.5 && (visible_round != new_round || visible_timeslice != new_timeslice)) {
        show_canon_board_slice(new_round, new_timeslice);
    }

}
animation_manager.change_round_cleanup = function(animation_args) {
    // Hide the animation overlay
    document.getElementById("board_animation_overlay").style.visibility = "hidden";
    document.getElementById("board_animation_overlay").style.transform = "";

    set_timeslice_navigation(true);

}

// -------------------- Dictionary of shift_frame methods ---------------------
// shift_frame_dictionary["animation_type"] = [preparation_method, get_frame_method, cleanup_method]
// animation_specs_dictionary["animation_type"] = [total_frames, frame_latency (in ms)]

animation_manager.add_animation("change_process", {
    "preparation" : animation_manager.change_process_preparation,
    "frame" : animation_manager.change_process_get_frame,
    "cleanup" : animation_manager.change_process_cleanup,
    "total_frames" : 40,
    "frame_latency" : 5
});
animation_manager.add_animation("change_round", {
    "preparation" : animation_manager.change_round_preparation,
    "frame" : animation_manager.change_round_get_frame,
    "cleanup" : animation_manager.change_round_cleanup,
    "total_frames" : 100,
    "frame_latency" : 2
});


// ----------------------------------------------------------------------------
// -------------------------------- Cameraman ---------------------------------
// ----------------------------------------------------------------------------
// This object is concerned with repositioning all the objects in board_window
// as the camera moves.

const cameraman = new Object();
cameraman.camera_zoom_status = "idle";
cameraman.camera_move_keys_pressed = 0;
cameraman.camera_move_directions = {"w" : false, "d" : false, "s" : false, "a" : false};
cameraman.camera_zoom_daemon = null;
cameraman.camera_zoom_directions = {"in" : false, "out" : false};
cameraman.camera_move_daemon = null;
// Manimpulation constants
cameraman.zoom_speed = 1.01;
cameraman.movement_speed = 0.003;
cameraman.refresh_rate = 5; // ms
// Position of the camera centre
cameraman.cx = 0.5;
cameraman.cy = 0.5;
// The camera forces a square aspect ratio, and hence the field-of-view size is
// parametrised by a single parameter, here chosen to represent the coefficient
// of the base length of a board square
cameraman.fov_coef = 1.0;
// Tracking properties
cameraman.tracking_stone = null;
cameraman.is_tracking_stone_onscreen = false;
cameraman.used_by_an_animation = false;

// --------------------------------- Methods ----------------------------------

cameraman.put_down_tripod = function() {
    // Find the default setting, which just about displays the entire board
    let default_width_fov_coef = board_window_width / (x_dim * 100);
    let default_height_fov_coef = board_window_height / (y_dim * 100);
    cameraman.default_fov_coef = Math.min(default_width_fov_coef, default_height_fov_coef); // This is also the max value!
    cameraman.max_fov_coef = board_window_width / 400;
    // Find an offset which places the middle of the board into the middle of the board window
    cameraman.offset_x = board_window_width * 0.5 - x_dim * 50;
    cameraman.offset_y = board_window_height * 0.5 - y_dim * 50;

    // Find and store the element which is target to camera's transformations
    cameraman.subject = document.getElementById("camera_subject");
}

cameraman.apply_camera = function() {
    cameraman.subject.style.transform = `translate(${cameraman.offset_x + x_dim * 100 * (0.5 - cameraman.cx) * cameraman.fov_coef}px,${cameraman.offset_y + y_dim * 100 * (0.5 - cameraman.cy) * cameraman.fov_coef}px) scale(${cameraman.fov_coef})`;
}

cameraman.apply_tracking = function(tracking_stone_state = null) {
    // tracking_stone_state is used mid-animations
    if (!(inspector.selection_mode_enabled)) {
        if (tracking_stone_state == null) {
            if (cameraman.tracking_stone != null) {
                if (stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone] != null) {
                    cameraman.cx = (stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][0] + 0.5) / x_dim;
                    cameraman.cy = (stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][1] + 0.5) / y_dim;
                    cameraman.is_tracking_stone_onscreen = true;
                    if (visible_process == "canon") {
                        inspector.display_square_info(stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][0], stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][1]);
                        inspector.display_stone_info(stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][0], stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][1]);
                    }
                } else {
                    cameraman.is_tracking_stone_onscreen = false;
                    if (inspector.highlighted_square != null) {
                        inspector.display_highlighted_info();
                    }
                }
            } else {
                cameraman.is_tracking_stone_onscreen = false;
                if (inspector.highlighted_square != null) {
                    inspector.display_highlighted_info();
                }
            }
        } else {
            cameraman.cx = (tracking_stone_state[0] + 0.5) / x_dim;
            cameraman.cy = (tracking_stone_state[1] + 0.5) / y_dim;
            cameraman.is_tracking_stone_onscreen = true;
        }
    }
    cameraman.apply_camera();
}

// -------------------------- Camera stone tracking ---------------------------
// Tracking has the following effects:
//   1. A panel shows up at the bottom of Stone inspector, allowing the player
//      to view the endpoints of the stone's trajectory and turn off tracking
//   2. The camera follows the stone, affixing it to the centre of the window
//   3. Auto-selecting the stone's trajectory points for the Square inspector
// Tracking can be turned on in the following ways:
//   1. Clicking on a stone highlight
//   2. Clicking on the button "Track this stone" in the Stone inspector panel
//   3. Double-clicking an occupied square (NOPE)
// And it can be turned off in the following ways:
//   1. Clicking the "Turn off tracking" button in the tracking inspector
//   2. Resetting the camera, e.g. by pressing the "R" key
//   3. Turning on a different camera mode, e.g. "go to square"
cameraman.track_stone = function(stone_ID) {
    if (!inspector.selection_mode_enabled) {
        // If null, tracking is turned off

        // We refuse to track a stone not placed on the board in this round
        if (stone_ID != null && stone_endpoints[selected_round][stone_ID] == undefined) {
            alert("Stone not placed on board");
        } else {
            cameraman.tracking_stone = stone_ID;
            document.getElementById("stone_tracking_label").innerHTML = (stone_ID == null ? "Stone tracking off" : `Tracking a<br/>${stone_highlight(stone_ID)}.`);
            set_stone_highlight(null); // We turn off the highlight
            if (stone_ID == null) {
                // Hide tracking buttons
                document.getElementById("tracking_inspector_svg").style.visibility = "hidden"
            } else {
                // Show tracking buttons
                document.getElementById("tracking_inspector_svg").style.visibility = "visible"
            }
            cameraman.apply_tracking();
        }
    }
}


cameraman.reset_camera = function() {
    cameraman.fov_coef = cameraman.default_fov_coef;
    cameraman.cx = 0.5;
    cameraman.cy = 0.5;
    cameraman.track_stone(null);
    cameraman.apply_camera();
}


// ------------------------------ Camera zooming ------------------------------

cameraman.zoom_camera = function() {
    if (cameraman.camera_zoom_directions["in"] && (! cameraman.camera_zoom_directions["out"])) {
        cameraman.fov_coef = Math.min(cameraman.fov_coef * cameraman.zoom_speed, cameraman.max_fov_coef);
    } else if (cameraman.camera_zoom_directions["out"] && (! cameraman.camera_zoom_directions["in"])) {
        cameraman.fov_coef = Math.max(cameraman.fov_coef / cameraman.zoom_speed, cameraman.default_fov_coef);
    }
    if (!cameraman.used_by_an_animation) {
        cameraman.apply_camera();
    }
}

// ----------------------------- Camera movement ------------------------------

cameraman.move_camera = function() {
    if (!(cameraman.tracking_stone != null && cameraman.is_tracking_stone_onscreen)) {
        if (cameraman.camera_move_directions["w"]) {
            cameraman.cy -= cameraman.movement_speed / cameraman.fov_coef;
        }
        if (cameraman.camera_move_directions["d"]) {
            cameraman.cx += cameraman.movement_speed / cameraman.fov_coef;
        }
        if (cameraman.camera_move_directions["s"]) {
            cameraman.cy += cameraman.movement_speed / cameraman.fov_coef;
        }
        if (cameraman.camera_move_directions["a"]) {
            cameraman.cx -= cameraman.movement_speed / cameraman.fov_coef;
        }
        cameraman.cx = Math.max(0.0, Math.min(1.0, cameraman.cx));
        cameraman.cy = Math.max(0.0, Math.min(1.0, cameraman.cy));
        cameraman.apply_camera();
    }
}

cameraman.show_square = function(x, y) {
    cameraman.cx = (x + 0.5) / x_dim;
    cameraman.cy = (y + 0.5) / y_dim;
    cameraman.apply_camera();
}

// --------------------------- Camera event parsers ---------------------------

cameraman.move_key_down = function(move_key) {
    if (cameraman.camera_move_keys_pressed == 0) {
        cameraman.camera_move_daemon = setInterval(cameraman.move_camera, cameraman.refresh_rate);
    }
    if (!(cameraman.camera_move_directions[move_key])) {
        cameraman.camera_move_keys_pressed += 1;
        cameraman.camera_move_directions[move_key] = true;
    }
}

cameraman.move_key_up = function(move_key) {
    if (cameraman.camera_move_directions[move_key]) {
        cameraman.camera_move_keys_pressed -= 1;
        cameraman.camera_move_directions[move_key] = false;
    }
    if (cameraman.camera_move_keys_pressed == 0) {
        clearInterval(cameraman.camera_move_daemon);
    }
}

cameraman.zoom_key_down = function(zoom_key) {
    if (!(cameraman.camera_zoom_directions["in"] || cameraman.camera_zoom_directions["out"])) {
        cameraman.camera_zoom_daemon = setInterval(cameraman.zoom_camera, cameraman.refresh_rate);
    }
    if (!(cameraman.camera_zoom_directions[zoom_key])) {
        cameraman.camera_zoom_directions[zoom_key] = true;
    }
}

cameraman.zoom_key_up = function(zoom_key) {
    if (cameraman.camera_zoom_directions[zoom_key]) {
        cameraman.camera_zoom_directions[zoom_key] = false;
    }
    if (!(cameraman.camera_zoom_directions["in"] || cameraman.camera_zoom_directions["out"])) {
        clearInterval(cameraman.camera_zoom_daemon);
    }
}

var highlighted_stone = null;
function set_stone_highlight(stone_ID) {
    if (stone_ID != highlighted_stone && highlighted_stone != null) {
        // Change of the guard
        document.getElementById(`stone_${highlighted_stone}`).style.filter = "";
    }
    highlighted_stone = stone_ID
    if (stone_ID != null) {
        document.getElementById(`stone_${stone_ID}`).style.filter = "url(#spotlight)";
    }
}


function stone_highlight(stone_ID) {
    return `<span class=\"stone_highlight\" onmouseenter=\"set_stone_highlight(${stone_ID})\" onmouseleave=\"set_stone_highlight(null)\" onclick=\"cameraman.track_stone(${stone_ID})\">${stone_properties[stone_ID]["stone_type"].toUpperCase()} [P. ${stone_properties[stone_ID]["allegiance"]}]</span>`;
}

function square_highlight(t, x, y) {
    return `<span class=\"square_highlight\" onclick=\"go_to_square(${t},${x},${y})\">(${t},${x},${y})</tspan>`;
}

// ----------------------------------------------------------------------------
// ---------------------------------- Events ----------------------------------
// ----------------------------------------------------------------------------

function parse_keydown_event(event) {
    //alert(event.key);
    switch(event.key) {
        case "z":
            show_prev_timeslice();
            break;
        case "x":
            show_active_timeslice();
            break;
        case "c":
            show_next_timeslice();
            break;
        case "ArrowRight":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(1);
                document.getElementById(`azimuth_indicator_1`).style["fill-opacity"] = 0.7;
            } else {
                show_next_round();
            }
            break
        case "ArrowLeft":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(3);
                document.getElementById(`azimuth_indicator_3`).style["fill-opacity"] = 0.7;
            } else {
                show_prev_round();
            }
            break
        case "ArrowUp":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(0);
                document.getElementById(`azimuth_indicator_0`).style["fill-opacity"] = 0.7;
            } else {
                show_active_round();
            }
            break
        case "ArrowDown":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(2);
                document.getElementById(`azimuth_indicator_2`).style["fill-opacity"] = 0.7;
            }
            break
        case "q":
            cameraman.zoom_key_down("in");
            break;
        case "e":
            cameraman.zoom_key_down("out");
            break;
        case "r":
            if (cameraman.camera_zoom_status == "running") {
                clearInterval(cameraman.camera_zoom_daemon);
                cameraman.camera_zoom_status = "idle";
            }
            cameraman.reset_camera();
            break;
        case "f":
            if (cameraman.camera_zoom_status == "running") {
                clearInterval(cameraman.camera_zoom_daemon);
                cameraman.camera_zoom_status = "idle";
            }
            cameraman.fov_coef = 1.0;
            cameraman.apply_camera();
            break;
        case "w":
            cameraman.move_key_down(event.key);
            break;
        case "d":
            cameraman.move_key_down(event.key);
            break;
        case "s":
            cameraman.move_key_down(event.key);
            break;
        case "a":
            cameraman.move_key_down(event.key);
            break;
        case "Escape":
            // The "Escape" behaviour is highly contextual, and the different
            // contexts it affects are sorted by priority as follows:
            //   1. Exits selection mode if board is in selection mode--otherwise,
            //   2. turns off tracking if tracking exists--otherwise,
            //   3. unselects square if selected
            if (inspector.selection_mode_enabled) {
                inspector.turn_off_selection_mode();
            } else if (cameraman.tracking_stone != null) {
                cameraman.track_stone(null);
            } else if (inspector.highlighted_square != null) {
                inspector.unselect_all();
            }
            break;
        case "Enter":
            if (inspector.selection_mode_enabled && (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false && inspector.selection_mode_information_level["swap_effect"] == false)) {
                inspector.submit_selection();
            }
            break;

    }
}
function parse_keyup_event(event) {
    //alert(event.key);
    switch(event.key) {
        case "ArrowRight":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_1`).style["fill-opacity"] = 0.5;
            }
            break
        case "ArrowLeft":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_3`).style["fill-opacity"] = 0.5;
            }
            break
        case "ArrowUp":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_0`).style["fill-opacity"] = 0.5;
            }
            break
        case "ArrowDown":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_2`).style["fill-opacity"] = 0.5;
            }
            break
        case "q":
            cameraman.zoom_key_up("in");
            break;
        case "e":
            cameraman.zoom_key_up("out");
            break;
        case "w":
            cameraman.move_key_up(event.key);
            break;
        case "d":
            cameraman.move_key_up(event.key);
            break;
        case "s":
            cameraman.move_key_up(event.key);
            break;
        case "a":
            cameraman.move_key_up(event.key);
            break;

    }
}


function show_next_timeslice(){
    if (timeslice_navigation_enabled && (selected_timeslice < t_dim - 1)) {
        if (inspector.selection_mode_enabled) {
            inspector.unselect_square();
        }
        select_timeslice(selected_timeslice += 1);
        animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice - 1, "canon", false]]);
        for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
            animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice, process_keys[process_key_index], false]]);
        }
        animation_manager.add_to_queue(["reset_to_canon"]);
    }
}

function show_prev_timeslice(){
    if (timeslice_navigation_enabled && (selected_timeslice > 0)) {
        if (inspector.selection_mode_enabled) {
            inspector.unselect_square();
        }
        select_timeslice(selected_timeslice -= 1);
        for (let process_key_index = process_keys.length - 2; process_key_index >= 0; process_key_index--) {
            animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice + 1, process_keys[process_key_index], true]]);
        }
        animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice, "canon", true]]);
        animation_manager.add_to_queue(["reset_to_canon"]);
    }
}

function show_active_timeslice(){
    // Always shows the timeslice corresponding to current_turn
    if (timeslice_navigation_enabled) {
        if (inspector.selection_mode_enabled) {
            inspector.unselect_square();
        }
        animation_manager.clear_queue();
        select_timeslice(active_timeslice);
        show_canon_board_slice(selected_round, selected_timeslice);
        cameraman.apply_tracking();
    }
}

function show_next_round() {
    if (round_navigation_enabled && (selected_round < active_round)) {
        select_round(selected_round += 1);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, ">>", "up"], "reset_to_canon"]);
    }
}

function show_prev_round() {
    if (round_navigation_enabled && (selected_round > 0)) {
        select_round(selected_round -= 1);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, "<<", "down"], "reset_to_canon"]);
    }
}

function show_active_round() {
    if (round_navigation_enabled && (selected_round != active_round)) {
        select_round(active_round);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, ">|", "up"], "reset_to_canon"]);
    }
}


// -------------------------------- Commander ---------------------------------
// Commander makes sure submission of commands is only possible once every c.f.
// stone has had a command specified, and marks stones to be commanded.
// Stones to be commanded: red square below. Commanded circles: green square.

const commander = new Object();
commander.command_checklist = [];
commander.touch_order = [];
commander.initialise_command_checklist = function() {
    for (i = 0; i < stones_to_be_commanded.length; i++) {
        commander.add_to_checklist(stones_to_be_commanded[i]);
    }
    commander.toggle_form_submission();
}

commander.add_to_checklist = function(stone_ID) {
    commander.command_checklist.push(stone_ID);
    if (commander.touch_order.includes(stone_ID)) {
        commander.touch_order.splice(commander.touch_order.indexOf(stone_ID), 1);
    }
    document.getElementById(`command_marker_${stone_ID}`).style.stroke = "red";
    document.getElementById(`command_marker_${stone_ID}`).style.display = "block";
    commander.toggle_form_submission();
}

commander.mark_as_checked = function(stone_ID) {
    commander.command_checklist.splice(commander.command_checklist.indexOf(stone_ID), 1);
    commander.touch_order.push(stone_ID);
    document.getElementById(`command_marker_${stone_ID}`).style.stroke = "green";
    commander.toggle_form_submission();
}

commander.update_meta_inputs = function() {
    // updated the meta fieldset of command form
    document.getElementById("touch_order_input").value = commander.touch_order.toString();
}

commander.toggle_form_submission = function() {
    if (commander.command_checklist.length > 0 || did_player_finish_turn) {
        document.getElementById("submit_commands_button").style.display = "none";
    } else {
        commander.update_meta_inputs();
        document.getElementById("submit_commands_button").style.display = "block";
    }
}

// -------------------------------- Inspector ---------------------------------

const inspector = new Object();
inspector.inspector_elements = {
    "stone" : {"title" : null, "containers" : new Object(), "values" : new Object()},
    "square" : {"title" : null, "containers" : new Object(), "values" : new Object()}
}
inspector.record_inspector_elements = function(which_inspector, element_name_list) {
    element_name_list.forEach(function(element_name, element_index) {
        inspector.inspector_elements[which_inspector]["containers"][element_name] = document.getElementById(`${which_inspector}_info_${element_name}_container`);
        inspector.inspector_elements[which_inspector]["values"][element_name] = document.getElementById(`${which_inspector}_info_${element_name}`);
    });
    inspector.inspector_elements[which_inspector]["title"] = document.getElementById(`${which_inspector}_inspector_title`);
}
inspector.display_value_list = function(which_inspector, element_name, value_list) {
    if (value_list.length == 0) {
        inspector.inspector_elements[which_inspector]["containers"][element_name].style.display = "none";
    } else {
        inspector.inspector_elements[which_inspector]["containers"][element_name].style.display = "block";
        html_object = "";
        for (let i = 0; i < value_list.length; i++) {
            html_object += `<p>${value_list[i]}</p>\n`;
        }
        inspector.inspector_elements[which_inspector]["values"][element_name].innerHTML = html_object;
    }
}


inspector.record_inspector_elements("stone", ["allegiance", "stone_type", "startpoint", "endpoint"]);
inspector.record_inspector_elements("square", ["active_effects", "activated_causes", "inactive_effects", "not_activated_causes"]);

inspector.reverse_causality_flags = []; // [round_n] = {"causes" : {"activated" : [], "not_activated" : [], "buffered" : []}, "effects" : {"active" : [], "inactive" : []}}
inspector.organise_reverse_causality_flags = function() {
    for (let round_n = 0; round_n <= active_round; round_n++) {
        inspector.reverse_causality_flags.push(new Object());
        inspector.reverse_causality_flags[round_n]["causes"] = {
            "activated" : [],
            "not_activated" : []
        }
        inspector.reverse_causality_flags[round_n]["effects"] = {
            "active" : [],
            "inactive" : [],
            "buffered" : []
        }
        // First, we check the non-buffered flags
        for (let passed_round_n = 0; passed_round_n < round_n; passed_round_n++) {
            for (let effect_i = 0; effect_i < effects[passed_round_n].length; effect_i++) {
                // Is effect active?
                if (scenarios[round_n]["effect_activity_map"][effects[passed_round_n][effect_i]]) {
                    inspector.reverse_causality_flags[round_n]["effects"]["active"].push(effects[passed_round_n][effect_i]);
                    // NOTE: If swapping, the corresponding cause may have been added on the last round, and will be encountered again!
                    inspector.reverse_causality_flags[round_n]["causes"]["activated"].push(scenarios[round_n]["effect_cause_map"][effects[passed_round_n][effect_i]]);
                } else {
                    inspector.reverse_causality_flags[round_n]["effects"]["inactive"].push(effects[passed_round_n][effect_i]);
                }

            }
            // Now we add the omitted non-buffered causes as not activated
            for (let cause_i = 0; cause_i < causes[passed_round_n].length; cause_i++) {
                // Is cause not activated?
                if (!(inspector.reverse_causality_flags[round_n]["causes"]["activated"].includes(causes[passed_round_n][cause_i]))) {
                    inspector.reverse_causality_flags[round_n]["causes"]["not_activated"].push(causes[passed_round_n][cause_i]);
                }

            }
        }
        // Now for the buffered flags: the effects are always inactive, for causes, it depends on the stone trajectory
        for (let effect_i = 0; effect_i < effects[round_n].length; effect_i++) {
            inspector.reverse_causality_flags[round_n]["effects"]["buffered"].push(effects[round_n][effect_i]);
        }
        for (let cause_i = 0; cause_i < causes[round_n].length; cause_i++) {
            if (!(inspector.reverse_causality_flags[round_n]["causes"]["activated"].includes(causes[round_n][cause_i]) || inspector.reverse_causality_flags[round_n]["causes"]["not_activated"].includes(causes[round_n][cause_i]))) {
                if (activated_buffered_causes[round_n].includes(causes[round_n][cause_i])) {
                    inspector.reverse_causality_flags[round_n]["causes"]["activated"].push(causes[round_n][cause_i]);
                } else {
                    inspector.reverse_causality_flags[round_n]["causes"]["not_activated"].push(causes[round_n][cause_i]);
                }
            }
        }
    }
}

// ----------------------- Human readable text methods ------------------------

inspector.human_readable_flag = function(action_role, flag_significance, flag_status, flag_ID) {
    // action_role defines the role of the flag in the sentence
    // flag_significance: cause or effect
    switch(action_role) {
        case "primary":
            switch(flag_significance) {
                case "effect":
                    switch(flag_status) {
                        case "active":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_in":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} time-jumps in`;
                                case "spawn_bomb":
                                    return `A bomb explodes`;

                            }
                        case "inactive":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_in":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} would time-jump in`;
                                case "spawn_bomb":
                                    return `A bomb would explode`;

                            }
                        case "buffered":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_in":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} is set to time-jump in`;
                                case "spawn_bomb":
                                    return `A bomb is set to explode`;

                            }
                    }
                case "cause":
                    switch(flag_status) {
                        case "activated":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_out":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} time-jumps out`;
                                case "attack":
                                    // switch stone type
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} (attacks? drops a bomb?)`;

                            }
                        case "not_activated":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_out":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} would time-jump out`;
                                case "attack":
                                    // switch stone type
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} (would attack? would drop a bomb?)`;

                            }
                    }
            }
        case "secondary":
            switch(flag_significance) {
                case "effect":
                    switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                        case "time_jump_in":
                            return `causing a ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} to time-jump in`;
                        case "spawn_bomb":
                            return `causing a bomb to explode`;

                    }
                case "cause":
                    switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                        case "time_jump_out":
                            return `caused by a ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} time-jumping out`;
                        case "attack":
                            // switch stone type
                            return `caused by a ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} (attacking? dropping a bomb?)`;

                    }
            }
    }
}

inspector.flag_description = function(flag_significance, flag_status, flag_ID) {
    // flag_significnce = effect or cause
    // NOTE: This function assumes selected_round is sane

    switch(flag_significance) {
        case "effect":
            primary_descriptor = inspector.human_readable_flag("primary", "effect", flag_status, flag_ID);
            if (["active", "buffered"].includes(flag_status)) {
                let corresponding_cause_ID = scenarios[selected_round]["effect_cause_map"][flag_ID];
                let cause_t = reverse_causality_flag_properties[corresponding_cause_ID]["t"];
                let cause_x = reverse_causality_flag_properties[corresponding_cause_ID]["x"];
                let cause_y = reverse_causality_flag_properties[corresponding_cause_ID]["y"];
                primary_descriptor += `, ${inspector.human_readable_flag("secondary", "cause", "activated", corresponding_cause_ID)} at ${square_highlight(cause_t, cause_x, cause_y)}`;
            }
            return primary_descriptor;
        case "cause":
            primary_descriptor = inspector.human_readable_flag("primary", "cause", flag_status, flag_ID);
            // We need to find the effect
            let corresponding_effect_ID = reverse_causality_flag_properties[flag_ID]["target_effect"];
            let corresponding_effect_status = undefined;
            let effect_statuses_to_try = ["active", "inactive", "buffered"];
            for (effect_status_index = 0; effect_status_index < effect_statuses_to_try.length; effect_status_index++) {
                if (inspector.reverse_causality_flags[selected_round]["effects"][effect_statuses_to_try[effect_status_index]].includes(corresponding_effect_ID)) {
                    corresponding_effect_status = effect_statuses_to_try[effect_status_index];
                    break;
                }
            }
            if (corresponding_effect_ID != undefined) {
                let effect_t = reverse_causality_flag_properties[corresponding_effect_ID]["t"];
                let effect_x = reverse_causality_flag_properties[corresponding_effect_ID]["x"];
                let effect_y = reverse_causality_flag_properties[corresponding_effect_ID]["y"];
                primary_descriptor += `, ${inspector.human_readable_flag("secondary", "effect", corresponding_effect_status, corresponding_effect_ID)} at ${square_highlight(effect_t, effect_x, effect_y)}`;
            }
            return primary_descriptor;
    }
}

inspector.endpoint_description = function(endpoint_event) {
    switch(endpoint_event) {
        case "setup":
            return "placed on setup";
        case "TJI":
            return "time-jumps-in";
        case "TJO":
            return "time-jumps-out";
        case "destruction":
            return "is destroyed";
        case "causally_free":
            return "becomes causally free";
        case "tag_locked":
            return "is tag-locked";
        default:
            return "UNKNOWN EVENT";
    }
}

// ---------------------------- Stone info methods ----------------------------

// Selection mode methods

// Information level: for every "true", the user needs to specify the value of
// the corresponding arg key before submitting the command and exiting sel. m.
inspector.selection_mode_enabled = false;
inspector.selection_mode_stone_ID = null;
inspector.selection_mode_information_level = {"square" : false, "azimuth" : false, "swap_effect" : false};
inspector.selection = {"square" : "NOT_SELECTED", "azimuth" : "NOT_SELECTED", "swap_effect" : "NOT_SELECTED"};
inspector.selection_submission = null;

inspector.selection_mode_options = new Object();

inspector.selection_keywords = ["stone_ID",
            "type",
            "t",
            "x",
            "y",
            "a",
            "target_t",
            "target_x",
            "target_y",
            "target_a",
            "swap_effect"];

inspector.turn_on_selection_mode = function(stone_ID, selection_mode_props) {
    cameraman.track_stone(null);
    inspector.selection_mode_enabled = true;
    // Commit current selection options to cache
    inspector.selection_mode_options = selection_mode_props;
    inspector.selection_mode_stone_ID = stone_ID;

    inspector.selection_mode_information_level["square"] = true;
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.selection_mode_information_level["swap_effect"] = true;
    inspector.selection_mode_information_level["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["swap_effect"] = "NOT_SELECTED";

    // Interrupt animations, disable tracking, force active round, disable round navigation, show selection highlights
    animation_manager.clear_queue();
    set_round_navigation(false);
    select_round(active_round);
    inspector.set_square_highlight(null);
    if (inspector.selection_mode_options["lock_timeslice"] != null) {
        set_timeslice_navigation(false);
        select_timeslice(inspector.selection_mode_options["lock_timeslice"]);
    } else if (inspector.selection_mode_options["squares"].length == 1) {
        set_timeslice_navigation(false);
        select_timeslice(inspector.selection_mode_options["squares"][0]["t"]);
    }
    document.getElementById("selection_mode_highlights").style.visibility = "visible";

    // Replace trackers with selectors
    document.getElementById("tracking_inspector").style.display = "none";
    document.getElementById("square_inspector").style.display = "none";
    document.getElementById("choice_selector").style.display = "block";
    document.getElementById("swap_effect_selector").style.display = "block";

    if (inspector.selection_mode_options["squares"].length == 1) {
        // The square is chosen automatically
        inspector.select_square(inspector.selection_mode_options["squares"][0]["x"], inspector.selection_mode_options["squares"][0]["y"]);
    }

    // Remove command buttons, create abort button
    let stone_inspector_commands_svg = document.getElementById("stone_inspector_commands_svg");
    while (stone_inspector_commands_svg.firstChild) {
        stone_inspector_commands_svg.removeChild(stone_inspector_commands_svg.lastChild);
    }
    document.getElementById("stone_inspector_commands_svg").style.display = "none";
    document.getElementById("abort_selection_button").style.display = "block";


    show_canon_board_slice(selected_round, selected_timeslice);

}

inspector.turn_off_selection_mode = function() {

    // Enable round navigation
    animation_manager.clear_queue();
    set_round_navigation(true);
    set_timeslice_navigation(true);

    // Hide highlights and dummies and azimuth indicators
    document.getElementById("selection_mode_highlights").style.visibility = "hidden";
    selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
    for (i = 0; i < selection_mode_dummies.length; i++) {
        selection_mode_dummies[i].style.display = "none";
    }
    for (ind_a = 0; ind_a < 4; ind_a++) {
        document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "none";
    }

    // Hide selection mode buttons
    document.getElementById("abort_selection_button").style.display = "none";
    document.getElementById("submit_selection_button").style.display = "none";
    document.getElementById("stone_inspector_commands_svg").style.display = "block";

    // Remove swap effect selection options
    inspector.unselect_swap_effect();

    // Replace selectors with trackers
    document.getElementById("choice_selector").style.display = "none";
    document.getElementById("swap_effect_selector").style.display = "none";
    document.getElementById("tracking_inspector").style.display = "block";
    document.getElementById("square_inspector").style.display = "block";


    inspector.selection_mode_enabled = false;


    select_round(active_round);
    select_timeslice(active_timeslice);

    show_canon_board_slice(selected_round, selected_timeslice);

    inspector.board_square_click(stone_trajectories[active_round][active_timeslice]["canon"][inspector.selection_mode_stone_ID][0], stone_trajectories[active_round][active_timeslice]["canon"][inspector.selection_mode_stone_ID][1]);

    // Clear cache
    inspector.selection_mode_options = null;
    inspector.selection_submission = null;
    inspector.selection_mode_stone_ID = null;

}

inspector.toggle_submit_button = function() {
    if (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false && inspector.selection_mode_information_level["swap_effect"] == false) {
        document.getElementById("submit_selection_button").style.display = "inline";
    } else {
        document.getElementById("submit_selection_button").style.display = "none";
    }
}

inspector.add_swap_effect_option = function(effect_ID) {
    let swap_effect_table = document.getElementById("swap_effect_selector_table");
    let option_id;
    let option_onclick;
    let option_button;
    let option_desc;
    if (effect_ID == null) {
        option_id = "swap_effect_option_null";
        option_onclick = "inspector.select_swap_effect(null)";
        option_button = "No swap";
        option_desc = "";
    } else {
        option_id = `swap_effect_option_${effect_ID}`;
        option_onclick = `inspector.select_swap_effect(${effect_ID})`;
        option_button = "Swap";
        option_desc = "unknown effect";
        // Check if active or inactive

        // Active effects
        for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["active"].length; effect_i++) {
            if (inspector.reverse_causality_flags[selected_round]["effects"]["active"][effect_i] == effect_ID) {
                // Is active
                option_desc = inspector.flag_description("effect", "active", effect_ID)
            }
        }
        // Inactive effects
        for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["inactive"].length; effect_i++) {
            if (inspector.reverse_causality_flags[selected_round]["effects"]["active"][effect_i] == effect_ID) {
                // Is inactive
                option_desc = inspector.flag_description("effect", "inactive", effect_ID)
            }
        }
    }
    let option_row = swap_effect_table.insertRow(-1);
    option_row.setAttribute("id", option_id);
    option_row.setAttribute("class", "swap_effect_option");
    let option_button_element = option_row.insertCell(0);
    option_button_element.setAttribute("id", `${option_id}_button`);
    option_button_element.setAttribute("class", "swap_effect_option_button");
    option_button_element.setAttribute("onclick", option_onclick);
    option_button_element.innerHTML = option_button;
    let option_desc_element = option_row.insertCell(1);
    option_desc_element.setAttribute("id", `${option_id}_description`);
    option_desc_element.setAttribute("class", "swap_effect_option_description");
    option_desc_element.innerHTML = option_desc;
}

inspector.select_square = function(x, y) {
    // We find the correct element of squares
    for (let i = 0; i < inspector.selection_mode_options["squares"].length; i++) {
        if (inspector.selection_mode_options["squares"][i]["t"] == selected_timeslice && inspector.selection_mode_options["squares"][i]["x"] == x && inspector.selection_mode_options["squares"][i]["y"] == y) {
            animation_manager.clear_queue();
            show_canon_board_slice(selected_round, selected_timeslice);
            let cur_square = inspector.selection_mode_options["squares"][i];
            inspector.selection["square"] = i;
            inspector.selection_mode_information_level["square"] = false;
            inspector.set_square_highlight([x, y]);
            if (cur_square["a"] != null) {
                if (cur_square["a"].length == 1) {
                    inspector.select_azimuth(cur_square["a"][0]);
                } else {
                    inspector.selection["azimuth"] = "NOT_SELECTED";
                    inspector.selection_mode_information_level["azimuth"] = true;
                }
            } else {
                inspector.select_azimuth(null);
            }

            inspector.unselect_swap_effect();
            if (cur_square["swap_effects"] != null) {
                for (ind_swap = 0; ind_swap < cur_square["swap_effects"].length; ind_swap++) {
                    inspector.add_swap_effect_option(cur_square["swap_effects"][ind_swap]);
                }

                if (cur_square["swap_effects"].length == 1) {
                    inspector.select_swap_effect(cur_square["swap_effects"][0]);
                } else {
                    inspector.selection["swap_effect"] = "NOT_SELECTED";
                    inspector.selection_mode_information_level["swap_effect"] = true;
                }
            } else {
                inspector.selection["swap_effect"] = null;
                inspector.selection_mode_information_level["swap_effect"] = false;
            }

            inspector.toggle_submit_button();
            show_canon_board_slice(selected_round, selected_timeslice);

            // Now, based on what we know and what is yet to be inputted, we show and hide the azimuth and swap_effect dialogues
            if (inspector.selection_mode_information_level["azimuth"]) {
                for (ind_a = 0; ind_a < 4; ind_a++) {
                    if (cur_square["a"].includes(ind_a)) {
                        document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "inline";
                    } else {
                        document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "none";
                    }
                }
            } else {
                for (ind_a = 0; ind_a < 4; ind_a++) {
                    document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "none";
                }
            }
        }
    }
}

inspector.unselect_square = function() {
    inspector.selection["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["square"] = true;
    inspector.set_square_highlight(null);
    inspector.unselect_swap_effect();
    let selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
    for (i = 0; i < selection_mode_dummies.length; i++) {
        selection_mode_dummies[i].style.display = "none";
    }
    inspector.selection["azimuth"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.selection["swap_effect"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["swap_effect"] = true;
    inspector.toggle_submit_button();
}

inspector.unselect_swap_effect = function() {
    // Clears cache, resets swap_effect selector
    inspector.selection["swap_effect"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["swap_effect"] = true;
    let swap_effect_table = document.getElementById("swap_effect_selector_table");
    while (swap_effect_table.firstChild) {
        swap_effect_table.removeChild(swap_effect_table.lastChild);
    }
}

inspector.select_azimuth = function(target_azimuth) {
    if (target_azimuth == null || inspector.selection_mode_options["squares"][inspector.selection["square"]]["a"].includes(target_azimuth)) {
        inspector.selection["azimuth"] = target_azimuth;
        inspector.selection_mode_information_level["azimuth"] = false;
        inspector.toggle_submit_button();
        console.log(`azimuth is known to be ${inspector.selection["azimuth"]}.`);
        show_canon_board_slice(selected_round, selected_timeslice);
    }
}

inspector.select_swap_effect = function(target_swap_effect) {
    if (target_swap_effect == null || inspector.selection_mode_options["squares"][inspector.selection["square"]]["swap_effects"].includes(target_swap_effect)) {
        inspector.selection["swap_effect"] = target_swap_effect;
        inspector.selection_mode_information_level["swap_effect"] = false;

        // Reset color of all elements, then color the selected element
        let swap_effect_option_buttons = document.getElementsByClassName("swap_effect_option_button");
        for (i = 0; i < swap_effect_option_buttons.length; i++) {
            swap_effect_option_buttons[i].style["background-color"] = "transparent";
        }
        document.getElementById(`swap_effect_option_${target_swap_effect}_button`).style["background-color"] = "lightgreen";

        inspector.toggle_submit_button();
        console.log(`swap effect is known to be ${inspector.selection["swap_effect"]}.`);
    }
}

inspector.submit_selection = function() {
    // onclick of the submit selection button
    // stores the command object in a hidden HTML dataform
    inspector.selection_submission["target_t"] = inspector.selection_mode_options["squares"][inspector.selection["square"]]["t"];
    inspector.selection_submission["target_x"] = inspector.selection_mode_options["squares"][inspector.selection["square"]]["x"];
    inspector.selection_submission["target_y"] = inspector.selection_mode_options["squares"][inspector.selection["square"]]["y"];
    inspector.selection_submission["target_a"] = inspector.selection["azimuth"];
    inspector.selection_submission["swap_effect"] = inspector.selection["swap_effect"];

    for (i = 0; i < inspector.selection_keywords.length; i++) {
        document.getElementById(`cmd_${inspector.selection_keywords[i]}_${inspector.selection_mode_stone_ID}`).value = inspector.selection_submission[inspector.selection_keywords[i]];
    }
    if (inspector.selection_mode_options["choice_keyword"] != null) {
        document.getElementById(`cmd_choice_keyword_${inspector.selection_mode_stone_ID}`).name = inspector.selection_mode_options["choice_keyword"];
        document.getElementById(`cmd_choice_keyword_${inspector.selection_mode_stone_ID}`).value = inspector.selection_submission["choice_keyword"];
    }

    commander.mark_as_checked(inspector.selection_mode_stone_ID);

    inspector.turn_off_selection_mode();

}


inspector.undo_command = function() {
    let stone_ID = find_stone_at_pos(inspector.highlighted_square[0], inspector.highlighted_square[1]);

    // Delete the values from the form
    for (i = 0; i < inspector.selection_keywords.length; i++) {
        document.getElementById(`cmd_${inspector.selection_keywords[i]}_${stone_ID}`).value = null;
    }
    document.getElementById(`cmd_choice_keyword_${stone_ID}`).name = `cmd_choice_keyword_${stone_ID}`;
    document.getElementById(`cmd_choice_keyword_${stone_ID}`).value = null;

    commander.add_to_checklist(stone_ID);
    inspector.display_stone_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
}

// Stone commands

inspector.prepare_command = function(stone_ID, command_key) {
    // Prompts user further to specify the arguments for the command
    console.log(`stone ${stone_ID} performs ${command_key}`);
    let cur_cmd_props = available_commands[stone_ID]["command_properties"][command_key];

    inspector.selection_submission = new Object();

    inspector.selection_submission["stone_ID"] = stone_ID;
    inspector.selection_submission["type"] = cur_cmd_props["command_type"];
    inspector.selection_submission["t"] = active_timeslice;
    inspector.selection_submission["x"] = stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID][0];
    inspector.selection_submission["y"] = stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID][1];
    inspector.selection_submission["a"] = stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID][2];

    inspector.turn_on_selection_mode(stone_ID, cur_cmd_props["selection_mode"]);

}

inspector.display_stone_commands = function(stone_ID) {
    document.getElementById("undo_command_button_svg").style.display = "none";
    document.getElementById("stone_inspector_commands_svg").style.display = "block";
    // if stone_ID = null, hides stone commands
    let stone_inspector_commands_svg = document.getElementById("stone_inspector_commands_svg");
    if (stone_ID == null) {
        while (stone_inspector_commands_svg.firstChild) {
            stone_inspector_commands_svg.removeChild(stone_inspector_commands_svg.lastChild);
        }
    } else {
        // First, we delete everything
        inspector.display_stone_commands(null);

        // Now, we find the list of commands
        let list_of_commands = available_commands[stone_ID]["commands"];

        // We draw every button
        offset_x = 0;
        offset_y = 0;
        for (let i = 0; i < list_of_commands.length; i++) {
            let new_button = make_SVG_element("rect", {
                class : "stone_command_panel_button",
                id : `stone_command_${list_of_commands[i]}`,
                onclick : `inspector.prepare_command(${stone_ID}, \"${list_of_commands[i]}\")`,
                x : offset_x,
                y : 0,
                width : stone_command_btn_width,
                height : stone_command_btn_height
            });
            let new_button_label = make_SVG_element("text", {
                class : "button_label",
                id : `stone_command_${list_of_commands[i]}_label`,
                x : offset_x + stone_command_btn_width / 2,
                y : stone_command_btn_height / 2,
                "text-anchor" : "middle"
            });
            new_button_label.textContent = available_commands[stone_ID]["command_properties"][list_of_commands[i]]["label"];
            stone_inspector_commands_svg.appendChild(new_button);
            stone_inspector_commands_svg.appendChild(new_button_label);
            offset_x += 110;

        }
    }
}

inspector.display_undo_button = function() {
    document.getElementById("stone_inspector_commands_svg").style.display = "none";
    document.getElementById("undo_command_button_svg").style.display = "block";
}



// General stone properties

inspector.display_stone_info = function(x, y) {
    // Is there even a stone present?
    let stone_ID = find_stone_at_pos(x, y);
    inspector.inspector_elements["stone"]["title"].innerHTML = (stone_ID == null ? "No stone selected" : `A ${stone_highlight(stone_ID)} selected`);

    if (stone_ID != null) {
        inspector.display_value_list("stone", "allegiance", [stone_properties[stone_ID]["allegiance"]]);
        inspector.display_value_list("stone", "stone_type", [stone_properties[stone_ID]["stone_type"].toUpperCase()]);
        inspector.display_value_list("stone", "startpoint", [`Stone ${inspector.endpoint_description(stone_endpoints[selected_round][stone_ID]["start"]["event"])} at ${square_highlight(stone_endpoints[selected_round][stone_ID]["start"]["t"], stone_endpoints[selected_round][stone_ID]["start"]["x"], stone_endpoints[selected_round][stone_ID]["start"]["y"])}`]);
        inspector.display_value_list("stone", "endpoint", [`Stone ${inspector.endpoint_description(stone_endpoints[selected_round][stone_ID]["end"]["event"])} at ${square_highlight(stone_endpoints[selected_round][stone_ID]["end"]["t"], stone_endpoints[selected_round][stone_ID]["end"]["x"], stone_endpoints[selected_round][stone_ID]["end"]["y"])}`]);

        // Check if can be commanded
        if (stones_to_be_commanded.includes(stone_ID) && selected_round == active_round && selected_timeslice == active_timeslice && arrays_equal(stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID].slice(0, 2), [x, y])) {
            if (commander.command_checklist.includes(stone_ID)) {
                // Display commands
                inspector.display_stone_commands(stone_ID);
            } else {
                inspector.display_undo_button();
            }
        } else {
            inspector.display_stone_commands(null);
        }

    } else {
        inspector.display_value_list("stone", "allegiance", []);
        inspector.display_value_list("stone", "stone_type", []);
        inspector.display_value_list("stone", "startpoint", []);
        inspector.display_value_list("stone", "endpoint", []);
        inspector.display_stone_commands(null);
    }

    return stone_ID;
}

inspector.hide_stone_info = function() {
    inspector.inspector_elements["stone"]["title"].innerHTML = "No stone selected";
    inspector.display_value_list("stone", "allegiance", []);
    inspector.display_value_list("stone", "stone_type", []);
    inspector.display_value_list("stone", "startpoint", []);
    inspector.display_value_list("stone", "endpoint", []);
}

// --------------------------- Square info methods ----------------------------

inspector.highlighted_square = null;
inspector.set_square_highlight = function(new_square) {
    if (inspector.highlighted_square != null) {
        if (new_square == null) {
            // Change of the guard
            document.getElementById(`square_highlighter`).style.display = "none";
        } else if(!arrays_equal(new_square, inspector.highlighted_square)) {
            // Change of the guard
            document.getElementById(`square_highlighter`).style.display = "none";
        }
    }
    inspector.highlighted_square = new_square;
    if (inspector.highlighted_square != null) {
        document.getElementById(`square_highlighter`).style.display = "inline";
        document.getElementById(`square_highlighter`).style.transform = `translate(${inspector.highlighted_square[0] * 100}px,${inspector.highlighted_square[1] * 100}px)`;
    }
}

inspector.display_square_info = function(x, y) {

    // First, we find all reverse-causality flags associated with this square
    let active_effects_message_list = [];
    let inactive_effects_message_list = [];
    let activated_causes_message_list = [];
    let not_activated_causes_message_list = [];
    // Active effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["active"].length; effect_i++) {
        let active_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["active"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(active_effect_ID, selected_timeslice, x, y)) {
            active_effects_message_list.push(inspector.flag_description("effect", "active", active_effect_ID));
        }
    }
    // Inactive effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["inactive"].length; effect_i++) {
        let inactive_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["inactive"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(inactive_effect_ID, selected_timeslice, x, y)) {
            inactive_effects_message_list.push(inspector.flag_description("effect", "inactive", inactive_effect_ID));
        }
    }
    // Buffered effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["buffered"].length; effect_i++) {
        let buffered_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["buffered"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(buffered_effect_ID, selected_timeslice, x, y)) {
            inactive_effects_message_list.push(inspector.flag_description("effect", "buffered", buffered_effect_ID));
        }
    }
    // Activated causes
    for (let cause_i = 0; cause_i < inspector.reverse_causality_flags[selected_round]["causes"]["activated"].length; cause_i++) {
        let activated_cause_ID = inspector.reverse_causality_flags[selected_round]["causes"]["activated"][cause_i];
        // Is flag at selected square?
        if (is_flag_at_pos(activated_cause_ID, selected_timeslice, x, y)) {
            activated_causes_message_list.push(inspector.flag_description("cause", "activated", activated_cause_ID));
        }
    }
    // Not activated causes
    for (let cause_i = 0; cause_i < inspector.reverse_causality_flags[selected_round]["causes"]["not_activated"].length; cause_i++) {
        let not_activated_cause_ID = inspector.reverse_causality_flags[selected_round]["causes"]["not_activated"][cause_i];
        // Is flag at selected square?
        if (is_flag_at_pos(not_activated_cause_ID, selected_timeslice, x, y)) {
            not_activated_causes_message_list.push(inspector.flag_description("cause", "not_activated", not_activated_cause_ID));
        }
    }

    // Display messages
    inspector.display_value_list("square", "active_effects", active_effects_message_list);
    inspector.display_value_list("square", "inactive_effects", inactive_effects_message_list);
    inspector.display_value_list("square", "activated_causes", activated_causes_message_list);
    inspector.display_value_list("square", "not_activated_causes", not_activated_causes_message_list);

    // Highligh square, reset stone highlight
    inspector.set_square_highlight([x, y]);
    inspector.inspector_elements["square"]["title"].innerHTML = `A SQUARE TYPE selected`;
    set_stone_highlight(null);
}


inspector.hide_square_info = function() {
    inspector.display_value_list("square", "active_effects", []);
    inspector.display_value_list("square", "inactive_effects", []);
    inspector.display_value_list("square", "activated_causes", []);
    inspector.display_value_list("square", "not_activated_causes", []);

    // Highligh square, reset stone highlight
    inspector.set_square_highlight(null);
    inspector.inspector_elements["square"]["title"].innerHTML = `No square selected`;
}

inspector.board_square_click = function(x, y){
    if (inspector.selection_mode_enabled) {
        for (let i = 0; i < inspector.selection_mode_options["squares"].length; i++) {
            if (inspector.selection_mode_options["squares"][i]["t"] == selected_timeslice && inspector.selection_mode_options["squares"][i]["x"] == x && inspector.selection_mode_options["squares"][i]["y"] == y) {
                inspector.select_square(x, y);
            }
        }
    } else {
        // We get information about the stone
        inspector.display_stone_info(x, y);
        // We get information about the square
        inspector.display_square_info(x, y);
    }
}

inspector.display_highlighted_info = function() {
    inspector.display_stone_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
    inspector.display_square_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
}

inspector.unselect_all = function() {
    inspector.hide_stone_info();
    inspector.hide_square_info();
}


function go_to_square(t, x, y, turn_off_tracking = true) {
    if (!inspector.selection_mode_enabled) {
        select_timeslice(t);
        show_stones_at_process(selected_round, selected_timeslice, "canon");
        show_time_jumps_at_time(selected_round, selected_timeslice);
        if (turn_off_tracking) {
            cameraman.track_stone(null);
        }
        cameraman.show_square(x, y);
        inspector.display_stone_info(x, y);
        inspector.display_square_info(x, y);
    }
}

function tracking_startpoint() {
    /*if (cameraman.tracking_stone != null) {
        if (stone_endpoints[selected_round][cameraman.tracking_stone] == undefined) {
            console.log("Stone not placed on board");
        } else {
            console.log(`Startpoint: ${stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["event"]} at (${stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["x"]}, ${stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["y"]})`);
        }
    }*/
    go_to_square(stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["t"], stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["x"], stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["y"], false)
}

function tracking_endpoint() {
    /*if (cameraman.tracking_stone != null) {
        if (stone_endpoints[selected_round][cameraman.tracking_stone] == undefined) {
            console.log("Stone not placed on board");
        } else {
            console.log(`Endpoint: ${stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["event"]} at (${stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["x"]}, ${stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["y"]})`);
        }
    }*/
    go_to_square(stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["t"], stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["x"], stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["y"], false)
}

// ----------------------------------------------------------------------------
// ------------------------------ Document setup ------------------------------
// ----------------------------------------------------------------------------

var all_factions = ["GM"].concat(factions)

var timeslice_navigation_enabled = true;
var round_navigation_enabled = true;

function set_timeslice_navigation(val) {
    timeslice_navigation_enabled = val;
    if (val) {
        let timeslice_buttons = document.getElementsByClassName("board_control_panel_button");
        for (i = 0; i < timeslice_buttons.length; i++) {
            timeslice_buttons[i].style.fill = "pink";
        }
    } else {
        let timeslice_buttons = document.getElementsByClassName("board_control_panel_button");
        for (i = 0; i < timeslice_buttons.length; i++) {
            timeslice_buttons[i].style.fill = "grey";
        }
    }
}

function set_round_navigation(val) {
    round_navigation_enabled = val;
    if (val) {
        let round_buttons = document.getElementsByClassName("game_control_panel_button");
        for (i = 0; i < round_buttons.length; i++) {
            round_buttons[i].style.fill = "pink";
        }
    } else {
        let round_buttons = document.getElementsByClassName("game_control_panel_button");
        for (i = 0; i < round_buttons.length; i++) {
            round_buttons[i].style.fill = "grey";
        }
    }
}

var selected_timeslice = 0; // this is the timeslice queued up to be displayed. The gameside label shows this number. Logic happens according to this number.
var visible_timeslice = 0; // this is the timeslice currently displayed by the animation. It is dragged by the animation and may not correspond to selected_timeslice.

let current_turn_props = round_from_turn(current_turn);

const active_round = current_turn_props[0];
const active_timeslice = current_turn_props[1];

// --------------------------- Fast animation setup ---------------------------

// initialise flat stone ID list for quick animations
var flat_stone_IDs = [];
all_factions.forEach(function(faction, faction_index) {
    faction_armies[faction].forEach(function(stone_ID, stone_index){
        flat_stone_IDs.push(stone_ID);
    });
});

// initialise inbetweens
// inbetweens[round][t][process] = {
//     "redundant" : true if start state and end state are equal
//     "cont_stones" : [list of stone IDs of stones existing at this process and next process],
//     "cont_stones_states" : [start_state_matrix, end_state_matrix],
//     "dest_stones" : [list of stone IDs destroyed by next process],
//     "dest_stones_states" : [state matrix for destroyed stones at this process],
//     "new_stones" : [list of stone IDs created by next process],
//     "new_stones_states" : [state matrix for created stones at next process],
//     "hide_stones" : [list of stone IDs of stones which are not placed on board at either this or the next process],
//     "new_time_jumps" : [list of used and unused time jump marker ids to fade in, corresponding list of types],
//     "old_time_jumps" : [list of used and unused time jump marker ids to fade out, corresponding list of types]
// }
const process_keys = ["flags", "pushes", "destructions", "tagscreens", "canon"];
const inbetweens = [];
for (let inbetween_round_index = 0; inbetween_round_index <= active_round; inbetween_round_index++) {
    inbetweens.push([]);
    for (let inbetween_time = 0; inbetween_time < t_dim; inbetween_time++) {
        inbetweens[inbetween_round_index].push(new Object());
        for (let inbetween_process_index = 0; inbetween_process_index < process_keys.length; inbetween_process_index++) {
            let start_process = process_keys[inbetween_process_index];
            inbetweens[inbetween_round_index][inbetween_time][start_process] = new Object();
            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones_states"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones_states"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["hide_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"] = [[], []];
            // We initialise the current inbetween
            if (inbetween_time == t_dim - 1 && start_process == "canon") {
                // This is the final state of the final timeslice, and therefore cannot be animated into a "next" state.
                inbetweens["redundant"] = true;
            } else {
                let is_redundant = true;

                let end_process;
                let end_time;
                if (start_process == "canon") {
                    end_process = process_keys[0];
                    end_time = inbetween_time + 1;
                } else {
                    end_process = process_keys[inbetween_process_index + 1];
                    end_time = inbetween_time;
                }
                // If start process is "tagscreens", then the animation shows stone and board actions. Therefore if any such actions exist, this animation is not redundant, even if no stone state changes.
                if (start_process == "tagscreens") {
                    if (stone_actions[inbetween_round_index][inbetween_time].length > 0) {
                        is_redundant = false;
                    }
                }

                for (let stone_ID_index = 0; stone_ID_index < flat_stone_IDs.length; stone_ID_index++) {
                    let start_state = stone_trajectories[inbetween_round_index][inbetween_time][start_process][flat_stone_IDs[stone_ID_index]];
                    let end_state = stone_trajectories[inbetween_round_index][end_time][end_process][flat_stone_IDs[stone_ID_index]];
                    if (start_state == null) {
                        if (end_state == null) {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["hide_stones"].push(flat_stone_IDs[stone_ID_index]);
                        } else {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones"].push(flat_stone_IDs[stone_ID_index]);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones_states"].push(end_state.slice());
                            is_redundant = false;
                        }
                    } else {
                        if (end_state == null) {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones"].push(flat_stone_IDs[stone_ID_index]);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones_states"].push(start_state.slice());
                            is_redundant = false;
                        } else {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones"].push(flat_stone_IDs[stone_ID_index]);
                            let start_state_copy = start_state.slice();
                            let end_state_copy = end_state.slice();
                            if (!(arrays_equal(start_state, end_state))) {
                                is_redundant = false;
                            }
                            // If the stone rotates, we want to choose the sensible rotation direction
                            if (end_state_copy[2] - start_state_copy[2] > 2) {
                                end_state_copy[2] -= 4;
                            }
                            if (end_state_copy[2] - start_state_copy[2] < -2) {
                                end_state_copy[2] += 4;
                            }
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"][0].push(start_state_copy);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"][1].push(end_state_copy);

                        }
                    }
                }

                // We check the time jump fades

                // If the end process is the first process in process_keys, if there are time jumps associated with end time, the animation is not redundant
                // Ditto for start process being "canon" and start time being associated with time jumps
                if (end_process == process_keys[0]) {
                    for (let x = 0; x < x_dim; x++) {
                        for (let y = 0; y < y_dim; y++) {
                            let used_tj_marker = inds(time_jumps[inbetween_round_index], [end_time, x, y, "used"]);
                            let unused_tj_marker = inds(time_jumps[inbetween_round_index], [end_time, x, y, "unused"]);
                            if (used_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][0].push(`used_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][1].push(`used_${used_tj_marker}`);
                                is_redundant = false;
                            }
                            if (unused_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][0].push(`unused_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][1].push(`unused_${unused_tj_marker}`);
                                is_redundant = false;
                            }
                        }
                    }
                }
                if (start_process == "canon") {
                    for (let x = 0; x < x_dim; x++) {
                        for (let y = 0; y < y_dim; y++) {
                            let used_tj_marker = inds(time_jumps[inbetween_round_index], [inbetween_time, x, y, "used"]);
                            let unused_tj_marker = inds(time_jumps[inbetween_round_index], [inbetween_time, x, y, "unused"]);
                            if (used_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][0].push(`used_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][1].push(`used_${used_tj_marker}`);
                                is_redundant = false;
                            }
                            if (unused_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][0].push(`unused_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][1].push(`unused_${unused_tj_marker}`);
                                is_redundant = false;
                            }
                        }
                    }
                }

                inbetweens[inbetween_round_index][inbetween_time][start_process]["redundant"] = is_redundant;
            }
        }
    }
}


// -------------------------- Initial display setup ---------------------------
var selected_round = active_round; // Selected by GUI logic, not affected by animations
var visible_round = selected_round; // Displayed by the GUI, affected by animations
var visible_process = "canon";

var selection_mode = false;

// Set up the camera
cameraman.put_down_tripod();
cameraman.reset_camera();

// Set up commander
commander.initialise_command_checklist();

// Set up inspector
inspector.organise_reverse_causality_flags();
inspector.hide_stone_info();
inspector.hide_square_info();

show_active_timeslice();
