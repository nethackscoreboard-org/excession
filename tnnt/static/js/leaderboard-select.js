function showLeaderboard(str) {
    /* This function unhides the div with class "leaderboard" and id
     * "leaderboard-<str>" and hides all others. */
    var boards = document.querySelectorAll('div.leaderboard-container')
    for (var b of boards) {
        // See also the HTML template where it relies on element ids matching
        // the values in the combo box
        if (b.id === 'leaderboard-' + str) {
            b.style.display = 'initial';
        }
        else {
            b.style.display = 'none';
        }
    }
}

function prevNextBoard(forward) {
    /* This function moves to the previous or next board according to their
     * order in the combo box element. */
    var combobox = document.getElementById('boards-combobox');
    if (!forward && combobox.selectedIndex > 0) {
        combobox.selectedIndex--;
        showLeaderboard(combobox.value);
    }
    else if (forward && combobox.selectedIndex + 1 < combobox.length) {
        combobox.selectedIndex++;
        showLeaderboard(combobox.value);
    }
}

document.addEventListener("DOMContentLoaded", function(event) {
    var combobox = document.getElementById('boards-combobox');
    // If the page is refreshed, the combobox may retain its old value, so show
    // that leaderboard.
    showLeaderboard(combobox.value);
    combobox.addEventListener('change', function(event) {
        showLeaderboard(combobox.value);
    });

    // set up event listeners for moving between boards without directly using
    // the combobox
    document.getElementById('prev-board').addEventListener('click', function(event) {
        prevNextBoard(false);
    });
    document.getElementById('next-board').addEventListener('click', function(event) {
        prevNextBoard(true);
    });
    document.addEventListener('keydown', function(event) {
        if ((event.code === "ArrowLeft" || event.code === "ArrowRight")
            && document.activeElement === combobox) {
            // if the combo box is in focus, assume the arrow keys will change
            // it and fire a change event, so do nothing here, otherwise we skip
            // over a board
            return;
        }
        if (event.code == "KeyH" || event.code == "ArrowLeft") {
            prevNextBoard(false);
        }
        if (event.code == "KeyL" || event.code == "ArrowRight") {
            prevNextBoard(true);
        }
    });
});
