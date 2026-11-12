
document.addEventListener("DOMContentLoaded", function () {

    const optimizeButton = document.getElementById("optimize-btn");
    const algorithmSelect = document.getElementById("algorithm-select");
    const statusMessage = document.getElementById("status-message");

    optimizeButton.addEventListener("click", function () {

        const markers = window.routeOptMarkers || [];

        if (markers.length < 2) {
            statusMessage.innerHTML =
                '<span class="status-message-icon">!</span>' +
                '<span>Please add at least 2 delivery points.</span>';

            return;
        }

        const algorithm = algorithmSelect.value;

        const algorithmNames = {
            nearest_neighbor: "Nearest Neighbor",
            two_opt: "Nearest Neighbor + 2-opt",
            nearest_insertion: "Nearest Insertion",
            farthest_insertion: "Farthest Insertion"
        };

        statusMessage.innerHTML =
            '<span class="status-message-icon">✦</span>' +
            '<span>Selected algorithm: ' +
            algorithmNames[algorithm] +
            '. Backend connection is not configured yet.</span>';
    });

});
