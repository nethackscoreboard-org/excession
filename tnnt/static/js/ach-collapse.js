document.addEventListener("DOMContentLoaded", function(event) {
    // set up event listener for showing or hiding the achievements table
    var hider = document.getElementById('ach-hide');
    hider.addEventListener('click', function(event) {
        var table = document.getElementById('achievements-table');
        var hider = document.getElementById('ach-hide');
        if (table.style.display === 'none') {
            table.style.display = 'block';
            hider.textContent = '[hide table]';
        }
        else {
            table.style.display = 'none';
            hider.textContent = '[show table]';
        }
    });
});
