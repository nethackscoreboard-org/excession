function showLeaderboard(str) {
    /* This function unhides the div with class "leaderboard" and id
     * "leaderboard-<str>" and hides all others. */
    var boards = document.querySelectorAll('div[class=leaderboard]')
    for (var b of boards) {
        // See also the HTML template where it relies on element ids matching
        // the values in the combo box
        if (b.id == 'leaderboard-' + str) {
            b.hidden = false;
        }
        else {
            b.hidden = true;
        }
    }
}

document.addEventListener("DOMContentLoaded", function(event) {
    var combobox = document.getElementById('boards-combobox')
    // If the page is refreshed, the combobox may retain its old value, so show
    // that leaderboard.
    showLeaderboard(combobox.value);
    combobox.addEventListener('change', function(event) {
        showLeaderboard(combobox.value);
    });
});
