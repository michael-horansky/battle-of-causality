
// Rendering constants
const board_square_rx = 2;
const board_square_ry = 2;
const board_square_fill = "blue";

const stone_rotation_offset = [[0, 0], [1, 0], [1, 1], [0, 1]];

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

// ---------------------------------- Events ----------------------------------

function show_timeslice(t){
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
    show_stones_at_process("canon");
}

function show_next_timeslice(){
    if (visible_timeslice < t_dim - 1) {
        show_timeslice(visible_timeslice + 1);
    } else{
        alert("No more timeslices to show");
    }
}

function show_prev_timeslice(){
    if (visible_timeslice > 0) {
        show_timeslice(visible_timeslice - 1);
    } else{
        alert("No more timeslices to show");
    }
}

function show_active_timeslice(){
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

function show_stones_at_process(process_key){
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            let stone_state = stone_trajectories[selected_turn][`${stone_ID}`][visible_timeslice][process_key]
            if (stone_state == null) {
                document.getElementById(`stone_${stone_ID}`).style.display = "none";
            } else {
                document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * (stone_state[0] + stone_rotation_offset[stone_state[2][0]][0])}px,${100 * (stone_state[1] + stone_rotation_offset[stone_state[2][0]][1])}px) rotate(${90 * stone_state[2][0]}deg)`;
                document.getElementById(`stone_${stone_ID}`).style.display = "inline";
            }
        });
    });
}



function board_square_click(t, x, y){
    alert(`This is a board square at time ${t} and position (${x}, ${y}).`);
}

var all_factions = ["GM"].concat(factions)

var visible_timeslice = 0;
var selected_turn = active_turn;

show_active_timeslice();
