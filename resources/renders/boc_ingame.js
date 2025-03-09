
// Rendering constants
const board_square_rx = 2;
const board_square_ry = 2;
const board_square_fill = "blue";

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

// ---------------------------------- Logic -----------------------------------

function round_from_turn(turn_index) {
    if (turn_index == 0) {
        return [0, -1];
    }
    let current_round_number = Math.floor((turn_index - 1) / t_dim);
    let current_timeslice    = (turn_index - 1) % t_dim;
    return [current_round_number, current_timeslice];
}

function cubic_bezier(t, x1, y1, x2, y2) {
    // t = 0 => 0
    // t = 1 => 1
    return (t*(t*(t+(1-t)*y2)+(1-t)*(t*y2+(1-t)*y1))+(1-t)*(t*(t*y2+(1-t)*y1)+(1-t)*(t*y1)));
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

/*function animated_transformation(val_start, val_end, total_frames, frame_key) {
    // val_start, val_end are numbers which denote the parameter to be animated
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return Math.round(val_start + (val_end - val_start) * frame_key / total_frames);
}*/

function animated_vector_transformation(vec_start, vec_end, total_frames, frame_key) {
    // vec_start, vec_end are vectors which denote the parameter to be animated
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return vec_round(vec_add(vec_start, vec_scale(vec_sub(vec_end, vec_start), frame_key / total_frames)));
}

function animated_matrix_transformation(mat_start, mat_end, total_frames, frame_key) {
    // mat_start, mat_end are matrices encoding the parameters to be animated.
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return mat_add(mat_start, mat_scale(mat_sub(mat_end, mat_start), cubic_bezier(frame_key / total_frames, 0.25, 0.1, 0.25, 1)));
}

// ---------------------------------- Events ----------------------------------

function parse_keydown_event(event) {
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
    }
}

function select_timeslice(new_timeslice) {
    selected_timeslice = new_timeslice;
    document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}; visible timeslice ${visible_timeslice}`;
}

function show_timeslice(t){
    select_timeslice(t);
    visible_timeslice = t;
    for (let cur_t = 0; cur_t < 6; cur_t++) {
        if (cur_t == t) {
            document.getElementById(`timeslice_${cur_t}`).style.display = "inline";
            //alert(`timeslice_${cur_t}`)
        } else {
            document.getElementById(`timeslice_${cur_t}`).style.display = "none";
            //alert("hiding " + cur_t)
        }
    }
    show_stones_at_process(selected_turn, selected_timeslice, "canon");
}

function show_active_timeslice(){
    animation_manager.clear_queue();
    let turn_props = round_from_turn(selected_turn);
    show_timeslice(turn_props[1]);
}

function hide_all_stones(){
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            document.getElementById(`stone_${stone_ID}`).style.display = "none";
        });
    });
}

function show_stones_at_process(turn, time, process_key){
    // NOT animated
    visible_timeslice = time;
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            let stone_state = stone_trajectories[turn][time][process_key][`${stone_ID}`];
            if (stone_state == null) {
                document.getElementById(`stone_${stone_ID}`).style.display = "none";
                displayed_stone_state[stone_ID] = null;
            } else {
                //document.getElementById(`stone_${stone_ID}`).addEventListener("transitionend", alert.bind(null, "lol"), false);
                document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * stone_state[0]}px,${100 * stone_state[1]}px) rotate(${90 * stone_state[2]}deg)`;
                //document.getElementById(`stone_${stone_ID}`).removeEventListener("transitionend", alert.bind(null, "lol"), false);
                document.getElementById(`stone_${stone_ID}`).style.display = "inline";
                displayed_stone_state[stone_ID] = stone_state;
            }
        });
    });
}

function hide_stones(local_stone_list) {
    local_stone_list.forEach(function(stone_ID, stone_index){
        document.getElementById(`stone_${stone_ID}`).style.display = "none";
    });
}

function show_stones_at_state(local_stone_list, state_matrix){
    // state_matrix[index in local_stone_list] = null or [x, y, azimuth]
    local_stone_list.forEach(function(stone_ID, stone_index){
        let stone_state = state_matrix[stone_index];
        if (stone_state == null) {
            document.getElementById(`stone_${stone_ID}`).style.display = "none";
            displayed_stone_state[stone_ID] = null;
        } else {
            //document.getElementById(`stone_${stone_ID}`).addEventListener("transitionend", alert.bind(null, "lol"), false);
            document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * stone_state[0]}px,${100 * stone_state[1]}px) rotate(${90 * stone_state[2]}deg)`;
            //document.getElementById(`stone_${stone_ID}`).removeEventListener("transitionend", alert.bind(null, "lol"), false);
            document.getElementById(`stone_${stone_ID}`).style.display = "inline";
            displayed_stone_state[stone_ID] = stone_state;
        }
    });
}

var animation_manager = new Object();
animation_manager.animation_queue = []; //[index] = [turn, s_time, s_process, play_backwards]
animation_manager.animation_daemon = null;
animation_manager.is_playing = false;
animation_manager.current_frame_key = 0;
animation_manager.total_frames = 40;
animation_manager.frame_latency = 5;
animation_manager.reset_animation = function() {
    animation_manager.animation_daemon = null;
    animation_manager.is_playing = false;
    animation_manager.current_frame_key = 0;
}
animation_manager.shift_frame = function(turn, s_time, s_process, play_backwards = false) {
    if (animation_manager.current_frame_key == animation_manager.total_frames) {
        clearInterval(animation_manager.animation_daemon);
        // animation cleanup
        //alert("This is the end of the animation!");
        if (play_backwards) {
            show_stones_at_process(turn, s_time, s_process);
        } else {
            if (s_process == "canon") {
                show_stones_at_process(turn, s_time + 1, process_keys[0]);
            } else {
                show_stones_at_process(turn, s_time, process_keys[process_keys.indexOf(s_process) + 1]);
            }
        }
        animation_manager.reset_animation();
        animation_manager.play_if_available();
    } else {
        animation_manager.current_frame_key += 1;
        //alert(animated_matrix_transformation(inbetweens[turn][start_time][start_process]["cont_stones_states"][0], inbetweens[turn][start_time][start_process]["cont_stones_states"][1], total_frames, cur_frame_key));
        show_stones_at_state(inbetweens[turn][s_time][s_process]["cont_stones"], animated_matrix_transformation(inbetweens[turn][s_time][s_process]["cont_stones_states"][0], inbetweens[turn][s_time][s_process]["cont_stones_states"][1], animation_manager.total_frames, (play_backwards ? animation_manager.total_frames - animation_manager.current_frame_key : animation_manager.current_frame_key)));
    }
}
animation_manager.play_if_available = function() {
    if (animation_manager.is_playing == false) {
        if (animation_manager.animation_queue.length > 0) {
            let current_animation = animation_manager.animation_queue.shift();
            animation_manager.is_playing = true;
            animation_manager.animation_daemon = setInterval(animation_manager.shift_frame, animation_manager.frame_latency, current_animation[0], current_animation[1], current_animation[2], current_animation[3]);
        }
    }
}
animation_manager.add_to_queue = function(list_of_animations) {
    list_of_animations.forEach(function(animation_args, index) {
        if (!(inbetweens[animation_args[0]][animation_args[1]][animation_args[2]]["redundant"])) {
            animation_manager.animation_queue.push(animation_args);
        }
    });
    //animation_manager.animation_queue = animation_manager.animation_queue.concat(list_of_animations);
    animation_manager.play_if_available();
}

animation_manager.clear_queue = function() {
    // clears queue and interrupts current animation
    clearInterval(animation_manager.animation_daemon);
    animation_manager.reset_animation();
    animation_manager.animation_queue = [];
}


function show_next_timeslice(){
    if (selected_timeslice < t_dim - 1) {
        //show_timeslice(selected_timeslice + 1);
        select_timeslice(selected_timeslice += 1);
        //animate_transition_between_states(selected_turn, selected_timeslice, "canon", 40, 5);
        animation_manager.add_to_queue([[selected_turn, selected_timeslice - 1, "canon", false]]);
        for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
            animation_manager.add_to_queue([[selected_turn, selected_timeslice, process_keys[process_key_index], false]]);
        }
    }
}

/*function show_prev_timeslice(){
    if (selected_timeslice > 0) {
        show_timeslice(selected_timeslice - 1);
    } else{
        alert("No more timeslices to show");
    }
}*/

function show_prev_timeslice(){
    if (selected_timeslice > 0) {
        select_timeslice(selected_timeslice -= 1);
        for (let process_key_index = process_keys.length - 2; process_key_index >= 0; process_key_index--) {
            animation_manager.add_to_queue([[selected_turn, selected_timeslice + 1, process_keys[process_key_index], true]]);
        }
        animation_manager.add_to_queue([[selected_turn, selected_timeslice, "canon", true]]);
    }
}


function board_square_click(t, x, y){
    alert(`This is a board square at time ${t} and position (${x}, ${y}).`);
}

var all_factions = ["GM"].concat(factions)

// ----------------------------------------------------------------------------
// --------------------------- Fast animation setup ---------------------------
// ----------------------------------------------------------------------------

// initialise flat stone ID list for quick animations
var flat_stone_IDs = [];
all_factions.forEach(function(faction, faction_index) {
    faction_armies[faction].forEach(function(stone_ID, stone_index){
        flat_stone_IDs.push(stone_ID);
    });
});

// initialise inbetweens
// inbetweens[turn][t][process] = {
//     "redundant" : true if start state and end state are equal
//     "cont_stones" : [list of stone IDs of stones existing at this process and next process],
//     "cont_stones_states" : [start_state_matrix, end_state_matrix],
//     "dest_stones" : [list of stone IDs destroyed by next process],
//     "dest_stones_states" : [state matrix for destroyed stones at this process],
//     "new_stones" : [list of stone IDs created by next process],
//     "new_stones_states" : [state matrix for created stones at next process],
//     "hide_stones" : [list of stone IDs of stones which are not placed on board at either this or the next process]
// }
const process_keys = ["flags", "pushes", "destructions", "tagscreens", "canon"];
const inbetweens = [];
for (let inbetween_turn_index = 0; inbetween_turn_index <= active_turn; inbetween_turn_index++) {
    inbetweens.push([]);
    for (let inbetween_time = 0; inbetween_time < t_dim; inbetween_time++) {
        inbetweens[inbetween_turn_index].push(new Object());
        for (let inbetween_process_index = 0; inbetween_process_index < process_keys.length; inbetween_process_index++) {
            let start_process = process_keys[inbetween_process_index];
            inbetweens[inbetween_turn_index][inbetween_time][start_process] = new Object();
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["cont_stones"] = [];
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["cont_stones_states"] = [[], []];
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["dest_stones"] = [];
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["dest_stones_states"] = [];
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["new_stones"] = [];
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["new_stones_states"] = [];
            inbetweens[inbetween_turn_index][inbetween_time][start_process]["hide_stones"] = [];
            // We initialise the current inbetween
            if (inbetween_time == t_dim - 1 && start_process == "canon") {
                // This is the final state of the final timeslice, and therefore cannot be animated into a "next" state.
                // By default, we set all stones as being destroyed or hidden
                /*for (let stone_ID_index = 0; stone_ID_index < flat_stone_IDs.length; stone_ID_index++) {
                    if (stone_trajectories[inbetween_turn_index][inbetween_time][start_process][flat_stone_IDs[stone_ID_index]] == null) {
                        inbetweens[inbetween_turn_index][inbetween_time][start_process]["hide_stones"].push(flat_stone_IDs[stone_ID_index]);
                    } else {
                        inbetweens[inbetween_turn_index][inbetween_time][start_process]["dest_stones"].push(flat_stone_IDs[stone_ID_index]);
                        inbetweens[inbetween_turn_index][inbetween_time][start_process]["dest_stones_states"].push(stone_trajectories[inbetween_turn_index][inbetween_time][start_process][flat_stone_IDs[stone_ID_index]].slice());
                    }
                }*/
                // actually we just set this as redundant
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

                for (let stone_ID_index = 0; stone_ID_index < flat_stone_IDs.length; stone_ID_index++) {
                    let start_state = stone_trajectories[inbetween_turn_index][inbetween_time][start_process][flat_stone_IDs[stone_ID_index]];
                    let end_state = stone_trajectories[inbetween_turn_index][end_time][end_process][flat_stone_IDs[stone_ID_index]];
                    if (start_state == null) {
                        if (end_state == null) {
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["hide_stones"].push(flat_stone_IDs[stone_ID_index]);
                        } else {
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["new_stones"].push(flat_stone_IDs[stone_ID_index]);
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["new_stones_states"].push(end_state.slice());
                            is_redundant = false;
                        }
                    } else {
                        if (end_state == null) {
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["dest_stones"].push(flat_stone_IDs[stone_ID_index]);
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["dest_stones_states"].push(start_state.slice());
                            is_redundant = false;
                        } else {
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["cont_stones"].push(flat_stone_IDs[stone_ID_index]);
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
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["cont_stones_states"][0].push(start_state_copy);
                            inbetweens[inbetween_turn_index][inbetween_time][start_process]["cont_stones_states"][1].push(end_state_copy);

                        }
                    }
                }
                inbetweens[inbetween_turn_index][inbetween_time][start_process]["redundant"] = is_redundant;
            }
        }
    }
}

write_to_html(`<p id="debug_log">This is the JavaScript debug log</p>`);
document.getElementById("debug_log").innerText = inbetweens[6][4]["canon"]["new_stones"];

// initialise displayed_stone_state
var displayed_stone_state = new Object();
all_factions.forEach(function(faction, faction_index) {
    faction_armies[faction].forEach(function(stone_ID, stone_index){
        displayed_stone_state[stone_ID] = null;
    });
});


var selected_timeslice = 0; // this is the timeslice queued up to be displayed. The gameside label shows this number. Logic happens according to this number.
var visible_timeslice = 0; // this is the timeslice currently displayed by the animation. It is dragged by the animation and may not correspond to selected_timeslice.
var selected_turn = active_turn;


show_active_timeslice();
