
if (typeof L === "undefined") {
    alert("Không tải được Leaflet. Hãy kiểm tra kết nối Internet!");
} else {
    const map = L.map("map");

    map.setView([16.0471, 108.2068], 5);

    // OpenStreetMap
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const deliveryMarkers = [];

    function updateLocationList() {
        const list = document.getElementById("location-list");

        list.innerHTML = "";

        if (deliveryMarkers.length === 0) {
            list.innerHTML =
                '<p class="empty-message">No delivery points yet.</p>';
        }

        deliveryMarkers.forEach((marker, index) => {
            const position = marker.getLatLng();

            const item = document.createElement("div");
            item.className = "location-item";

            const number = document.createElement("span");
            number.className = "location-number";
            number.textContent = String(index + 1).padStart(2, "0");

            const coordinate = document.createElement("span");
            coordinate.textContent =
                position.lat.toFixed(5) + ", " +
                position.lng.toFixed(5);

            item.appendChild(number);
            item.appendChild(coordinate);

            list.appendChild(item);
        });
    }

    function updateStatistics() {
        const total = deliveryMarkers.length;

        document.getElementById("total-locations").textContent = total;

        const display = document.getElementById("total-locations-display");

        if (display) {
            display.textContent = total;
        }
    }

    function addDeliveryPoint(latitude, longitude) {
        const marker = L.marker([latitude, longitude]).addTo(map);

        marker.bindPopup(
            "Delivery Point " + (deliveryMarkers.length + 1)
        );

        deliveryMarkers.push(marker);

        updateLocationList();
        updateStatistics();

        marker.openPopup();
    }

    // Click map to add a point
    map.on("click", function (event) {
        addDeliveryPoint(
            event.latlng.lat,
            event.latlng.lng
        );
    });

    // Clear all points
    document.getElementById("clear-markers-btn")
        .addEventListener("click", function () {

            deliveryMarkers.forEach(marker => {
                map.removeLayer(marker);
            });

            deliveryMarkers.length = 0;

            updateLocationList();
            updateStatistics();

            document.getElementById("status-message").innerHTML =
                '<span class="status-message-icon">✓</span>' +
                '<span>All delivery points have been cleared.</span>';

            document.getElementById("total-distance").innerHTML =
                '-- <small>km</small>';

            document.getElementById("improvement").textContent = "--%";
        });

    // Expose map data for other JavaScript files
    window.routeOptMap = map;
    window.routeOptMarkers = deliveryMarkers;
    window.addDeliveryPoint = addDeliveryPoint;

    updateLocationList();
    updateStatistics();

    console.log("RouteOpt Map loaded successfully!");
}
