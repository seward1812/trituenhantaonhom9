if (typeof L === "undefined") {
    alert("Không tải được Leaflet. Hãy kiểm tra kết nối Internet!");
} else {
    const map = L.map("map");
    map.setView([16.0471, 108.2068], 5);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    const deliveryMarkers = [];
    let depotMarker = null;

    function isCvrp() {
        return document.getElementById("mode-select")?.value === "cvrp";
    }

    function updateLocationList() {
        const list = document.getElementById("location-list");
        list.innerHTML = "";
        if (deliveryMarkers.length === 0) {
            list.innerHTML = '<p class="empty-message">No delivery points yet.</p>';
        }
        deliveryMarkers.forEach((marker, index) => {
            const position = marker.getLatLng();
            const item = document.createElement("div");
            item.className = "location-item";
            const number = document.createElement("span");
            number.className = "location-number";
            number.textContent = String(index + 1).padStart(2, "0");
            const content = document.createElement("span");
            content.className = "location-content";
            content.textContent = `${position.lat.toFixed(5)}, ${position.lng.toFixed(5)}`;
            if (isCvrp()) {
                const demand = document.createElement("input");
                demand.className = "demand-input";
                demand.type = "number";
                demand.min = "1";
                demand.step = "1";
                demand.value = marker.routeOptDemand ?? 1;
                demand.title = "Customer demand";
                demand.addEventListener("input", () => {
                    marker.routeOptDemand = demand.value;
                });
                content.appendChild(demand);
            }
            item.appendChild(number);
            item.appendChild(content);
            list.appendChild(item);
        });
    }

    function updateStatistics() {
        document.getElementById("total-locations").textContent = deliveryMarkers.length;
        const display = document.getElementById("total-locations-display");
        if (display) display.textContent = deliveryMarkers.length;
        const depotInfo = document.getElementById("depot-address");
        if (depotInfo) {
            depotInfo.textContent = depotMarker
                ? `Depot: ${depotMarker.getLatLng().lat.toFixed(5)}, ${depotMarker.getLatLng().lng.toFixed(5)}`
                : "Depot: Not selected";
        }
    }

    function setDepot(latitude, longitude) {
        if (depotMarker) map.removeLayer(depotMarker);
        depotMarker = L.marker([latitude, longitude], { title: "Depot" }).addTo(map);
        depotMarker.bindPopup("Depot").openPopup();
        updateStatistics();
    }

    function addDeliveryPoint(latitude, longitude) {
        const marker = L.marker([latitude, longitude]).addTo(map);
        marker.routeOptDemand = 1;
        marker.bindPopup(`Delivery Point ${deliveryMarkers.length + 1}`);
        deliveryMarkers.push(marker);
        updateLocationList();
        updateStatistics();
        marker.openPopup();
    }

    map.on("click", event => {
        if (isCvrp() && document.getElementById("map-mode-select")?.value === "depot") {
            setDepot(event.latlng.lat, event.latlng.lng);
        } else {
            addDeliveryPoint(event.latlng.lat, event.latlng.lng);
        }
    });

    document.getElementById("clear-markers-btn").addEventListener("click", () => {
        deliveryMarkers.forEach(marker => map.removeLayer(marker));
        deliveryMarkers.length = 0;
        if (depotMarker) map.removeLayer(depotMarker);
        depotMarker = null;
        updateLocationList();
        updateStatistics();
        document.getElementById("total-distance").innerHTML = "-- <small>km</small>";
        document.getElementById("improvement").textContent = "--%";
    });

    window.routeOptMap = map;
    window.routeOptMarkers = deliveryMarkers;
    window.routeOptGetDepot = () => depotMarker;
    window.routeOptSetDepot = setDepot;
    window.routeOptUpdateLocationList = updateLocationList;
    window.addDeliveryPoint = addDeliveryPoint;
    updateLocationList();
    updateStatistics();
}
