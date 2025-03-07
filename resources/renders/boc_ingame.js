
// Rendering constants
var board_square_rx = 2;
var board_square_ry = 2;
var board_square_fill = "blue";



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
    for (let cur_t = 0; cur_t < 6; cur_t++) {
        if (cur_t == t) {
            document.getElementById(`timeslice_${cur_t}`).style.display = "inline";
            //alert(`timeslice_${cur_t}`)
        } else {
            document.getElementById(`timeslice_${cur_t}`).style.display = "none";
            //alert("hiding " + cur_t)
        }
    }
}

function show_next_timeslice(){
    if (visible_timeslice < t_dim - 1) {
        visible_timeslice += 1;
        show_timeslice(visible_timeslice);
    } else{
        alert("No more timeslices to show");
    }
}

function show_prev_timeslice(){
    if (visible_timeslice > 0) {
        visible_timeslice -= 1;
        show_timeslice(visible_timeslice);
    } else{
        alert("No more timeslices to show");
    }
}

function show_active_timeslice(){
    let turn_props = round_from_turn(selected_turn);
    show_timeslice(turn_props[1]);
}

function board_square_click(t, x, y){
    alert(`This is a board square at time ${t} and position (${x}, ${y}).`);
}


var visible_timeslice = 0;
var selected_turn = active_turn;

show_timeslice(visible_timeslice);
