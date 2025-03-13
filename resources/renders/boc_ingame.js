
// ----------------------------------------------------------------------------
// --------------------------- Rendering constants ----------------------------
// ----------------------------------------------------------------------------
const board_window_width = 800;
const board_window_height = 700;


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
function vec_add(vec1,vec2){
    return vec1.map((e,i) => e + vec2[i]);
}

function vec_sub(vec1,vec2){
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
    return vec_add(vec_start, vec_scale(vec_sub(vec_end, vec_start), frame_key / total_frames));
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
    if (new_timeslice == null) {
        selected_timeslice = 0;
    } else {
        selected_timeslice = new_timeslice;
    }
    document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}, selected round ${selected_round}`;
}

function show_canon_board_slice(round_n, timeslice){
    visible_round = round_n;
    visible_timeslice = timeslice;
    show_stones_at_process(round_n, timeslice, "canon");
    show_time_jumps_at_time(round_n, timeslice);
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
            animation_manager.is_playing = true;
            // prepare contextual animation specifications
            animation_manager.total_frames = animation_manager.dictionary_of_animations[current_animation[0]]["total_frames"];
            animation_manager.frame_latency = animation_manager.dictionary_of_animations[current_animation[0]]["frame_latency"];
            animation_manager.dictionary_of_animations[current_animation[0]]["preparation"](current_animation.slice(1));
            animation_manager.animation_daemon = setInterval(animation_manager.shift_frame_method, animation_manager.frame_latency, current_animation);
        }
    }
}
animation_manager.add_to_queue = function(list_of_animations) {
    // Each animation is a list, where the first element is a key in dictionary_of_animations
    list_of_animations.forEach(function(animation_args, index) {
        switch(animation_args[0]) {
            case "change_process":
                if (!(inbetweens[animation_args[1]][animation_args[2]][animation_args[3]]["redundant"])) {
                    animation_manager.animation_queue.push(animation_args);
                }
                break;
            default:
                animation_manager.animation_queue.push(animation_args);
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
}

// change_round
animation_manager.change_round_preparation = function(animation_args) {
    let animation_overlay_msg = animation_args[2];
    let transition_direction = animation_args[3];
    // disable timeslice navigation
    timeslice_navigation_enabled = false;
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

    timeslice_navigation_enabled = true;

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

cameraman.reset_camera = function() {
    cameraman.fov_coef = cameraman.default_fov_coef;
    cameraman.cx = 0.5;
    cameraman.cy = 0.5;
    cameraman.apply_camera();
}

cameraman.zoom_in = function() {
    cameraman.fov_coef = Math.min(cameraman.fov_coef * cameraman.zoom_speed, cameraman.max_fov_coef);
    cameraman.apply_camera();
}
cameraman.zoom_out = function() {
    cameraman.fov_coef = Math.max(cameraman.fov_coef / cameraman.zoom_speed, cameraman.default_fov_coef);
    cameraman.apply_camera();
}
cameraman.move_camera = function() {
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
            show_next_round();
            break
        case "ArrowLeft":
            show_prev_round();
            break
        case "ArrowUp":
            show_active_round();
            break
        case "ArrowDown":
            break
        case "q":
            if (cameraman.camera_zoom_status == "idle") {
                cameraman.camera_zoom_status = "running";
                cameraman.camera_zoom_daemon = setInterval(cameraman.zoom_in, cameraman.refresh_rate);
            }
            break;
        case "e":
            if (cameraman.camera_zoom_status == "idle") {
                cameraman.camera_zoom_status = "running";
                cameraman.camera_zoom_daemon = setInterval(cameraman.zoom_out, cameraman.refresh_rate);
            }
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

    }
}
function parse_keyup_event(event) {
    //alert(event.key);
    switch(event.key) {
        case "q":
            clearInterval(cameraman.camera_zoom_daemon);
            cameraman.camera_zoom_status = "idle";
            break;
        case "e":
            clearInterval(cameraman.camera_zoom_daemon);
            cameraman.camera_zoom_status = "idle";
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
        select_timeslice(selected_timeslice += 1);
        animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice - 1, "canon", false]]);
        for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
            animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice, process_keys[process_key_index], false]]);
        }
    }
}

function show_prev_timeslice(){
    if (timeslice_navigation_enabled && (selected_timeslice > 0)) {
        select_timeslice(selected_timeslice -= 1);
        for (let process_key_index = process_keys.length - 2; process_key_index >= 0; process_key_index--) {
            animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice + 1, process_keys[process_key_index], true]]);
        }
        animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice, "canon", true]]);
    }
}

function show_active_timeslice(){
    // Always shows the timeslice corresponding to current_turn
    if (timeslice_navigation_enabled) {
        animation_manager.clear_queue();
        select_timeslice(active_timeslice);
        show_canon_board_slice(selected_round, selected_timeslice);
    }
}

function show_next_round() {
    if (round_navigation_enabled && (selected_round < active_round)) {
        select_round(selected_round += 1);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, ">>", "up"]]);
    }
}

function show_prev_round() {
    if (round_navigation_enabled && (selected_round > 0)) {
        select_round(selected_round -= 1);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, "<<", "down"]]);
    }
}

function show_active_round() {
    if (round_navigation_enabled && (selected_round != active_round)) {
        select_round(active_round);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, ">|", "up"]]);
    }
}

// -------------------------------- Inspector ---------------------------------

const inspector = new Object();
inspector.inspector_elements = {
    "stone" : new Object(),
    "square" : new Object()
}
inspector.record_inspector_elements = function(which_inspector, element_name_list) {
    element_name_list.forEach(function(element_name, element_index) {
        inspector.inspector_elements[which_inspector][element_name] = document.getElementById(`${which_inspector}_info_${element_name}`);
    });
}
inspector.display_value_list = function(which_inspector, element_name, value_list) {
    html_object = "";
    for (let i = 0; i < value_list.length; i++) {
        html_object += `<p>${value_list[i]}</p>\n`;
    }
    inspector.inspector_elements[which_inspector][element_name].innerHTML = html_object;
}


inspector.record_inspector_elements("stone", ["allegiance", "type", "startpoint", "endpoint"]);
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
        if (is_flag_at_pos(active_effect_ID, selected_timeslice - 1, x, y)) {
            active_effects_message_list.push(`${reverse_causality_flag_properties[active_effect_ID]["flag_type"]} happens here, caused by this and this`);
        }
    }
    // Inactive effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["inactive"].length; effect_i++) {
        let inactive_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["inactive"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(inactive_effect_ID, selected_timeslice - 1, x, y)) {
            inactive_effects_message_list.push(`${reverse_causality_flag_properties[inactive_effect_ID]["flag_type"]} would happen here.`);
        }
    }
    // Buffered effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["buffered"].length; effect_i++) {
        let buffered_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["buffered"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(buffered_effect_ID, selected_timeslice - 1, x, y)) {
            inactive_effects_message_list.push(`${reverse_causality_flag_properties[buffered_effect_ID]["flag_type"]} is dogmatic in the next round.`);
        }
    }
    // Activated causes
    for (let cause_i = 0; cause_i < inspector.reverse_causality_flags[selected_round]["causes"]["activated"].length; cause_i++) {
        let activated_cause_ID = inspector.reverse_causality_flags[selected_round]["causes"]["activated"][cause_i];
        // Is flag at selected square?
        if (is_flag_at_pos(activated_cause_ID, selected_timeslice, x, y)) {
            activated_causes_message_list.push(`${reverse_causality_flag_properties[activated_cause_ID]["flag_type"]} happens here, causing this and this`);
        }
    }
    // Not activated causes
    for (let cause_i = 0; cause_i < inspector.reverse_causality_flags[selected_round]["causes"]["not_activated"].length; cause_i++) {
        let not_activated_cause_ID = inspector.reverse_causality_flags[selected_round]["causes"]["not_activated"][cause_i];
        // Is flag at selected square?
        if (is_flag_at_pos(not_activated_cause_ID, selected_timeslice, x, y)) {
            not_activated_causes_message_list.push(`${reverse_causality_flag_properties[not_activated_cause_ID]["flag_type"]} would happen here, causing this and this`);
        }
    }

    // Display messages
    inspector.display_value_list("square", "active_effects", active_effects_message_list);
    inspector.display_value_list("square", "inactive_effects", inactive_effects_message_list);
    inspector.display_value_list("square", "activated_causes", activated_causes_message_list);
    inspector.display_value_list("square", "not_activated_causes", not_activated_causes_message_list);
}

inspector.board_square_click = function(x, y){
    // We get information about the square
    inspector.display_square_info(x, y);

}


// ----------------------------------------------------------------------------
// ------------------------------ Document setup ------------------------------
// ----------------------------------------------------------------------------

var all_factions = ["GM"].concat(factions)

var timeslice_navigation_enabled = true;
var round_navigation_enabled = true;

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
show_active_timeslice();

// Set up the camera
cameraman.put_down_tripod();
cameraman.reset_camera();

// Set up inspector
inspector.organise_reverse_causality_flags();
