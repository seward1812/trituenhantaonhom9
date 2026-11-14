document.addEventListener("DOMContentLoaded", function () {
    const optimizeButton = document.getElementById("optimize-btn");
    const algorithmSelect = document.getElementById("algorithm-select");
    const modeSelect = document.getElementById("mode-select");
    const cvrpControls = document.getElementById("cvrp-controls");
    const statusMessage = document.getElementById("status-message");
    const totalDistance = document.getElementById("total-distance");
    const improvementDisplay = document.getElementById("improvement");
    const comparisonBody = document.getElementById("comparison-body");
    const routeColors = ["#38bdf8", "#a78bfa", "#fb923c", "#22c55e", "#f472b6", "#facc15"];
    let routeLine = null;
    let routeLayers = [];

    const algorithmNames = {
        nearest_neighbor: "Nearest Neighbor",
        two_opt: "2-opt",
        nearest_insertion: "Nearest Insertion",
        farthest_insertion: "Farthest Insertion"
    };

    function showStatus(message, type = "info") {
        statusMessage.textContent = message;
        statusMessage.dataset.type = type;
    }

    function updateModeControls() {
        const cvrp = modeSelect.value === "cvrp";
        cvrpControls.hidden = !cvrp;
        if (window.routeOptUpdateLocationList) window.routeOptUpdateLocationList();
    }

    function clearRoutes() {
        const map = window.routeOptMap;
        if (map && routeLine) map.removeLayer(routeLine);
        routeLine = null;
        routeLayers.forEach(layer => {
            if (map) map.removeLayer(layer);
        });
        routeLayers = [];
        window.routeOptRouteLine = null;
    }

    function displayComparison(comparison, cvrp = false) {
        comparisonBody.innerHTML = "";
        if (!comparison || Object.keys(comparison).length === 0) {
            comparisonBody.innerHTML = '<tr><td colspan="4">No comparison data available.</td></tr>';
            return;
        }
        Object.entries(comparison).forEach(([algorithm, result]) => {
            const row = document.createElement("tr");
            const distance = Number(result.distance ?? result.optimization_distance_km ?? 0);
            const improvement = Number(result.improvement ?? 0);
            const detail = cvrp
                ? `${(result.routes || []).length} route(s), load ${(result.loads || []).join(", ")}`
                : (result.route ? `${result.route.length} points` : "-");
            row.innerHTML = `<td>${algorithmNames[algorithm] || algorithm}</td><td>${distance.toFixed(3)} km</td><td>${improvement.toFixed(2)}%</td><td>${detail}</td>`;
            comparisonBody.appendChild(row);
        });
    }

    function coordinatesFromGeometry(geometry) {
        if (!Array.isArray(geometry) || geometry.length < 2) throw new Error("OSRM returned invalid route geometry.");
        return geometry.map(coordinate => {
            const lng = Number(coordinate[0]);
            const lat = Number(coordinate[1]);
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) throw new Error("Invalid route coordinate.");
            return [lat, lng];
        });
    }

    function drawRoute(routeGeometry) {
        const map = window.routeOptMap;
        clearRoutes();
        const latLngs = coordinatesFromGeometry(routeGeometry);
        routeLine = L.polyline(latLngs, { color: "#38bdf8", weight: 5, opacity: 0.95 }).addTo(map);
        window.routeOptRouteLine = routeLine;
        map.fitBounds(routeLine.getBounds(), { padding: [40, 40] });
    }

    function drawRoutes(routeDetails) {
        const map = window.routeOptMap;
        clearRoutes();
        const bounds = [];
        routeDetails.forEach((detail, index) => {
            const layer = L.polyline(coordinatesFromGeometry(detail.geometry), {
                color: routeColors[index % routeColors.length], weight: 5, opacity: 0.9
            }).addTo(map);
            layer.bindPopup(`Vehicle ${detail.vehicle}: load ${detail.load}/${detail.capacity}, ${detail.distance_km.toFixed(3)} km`);
            routeLayers.push(layer);
            bounds.push(...layer.getLatLngs());
        });
        if (bounds.length) map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });
    }

    function buildCvrpPayload() {
        const markers = window.routeOptMarkers || [];
        const depotMarker = window.routeOptGetDepot && window.routeOptGetDepot();
        if (!depotMarker) throw new Error("Please set a depot before optimizing CVRP.");
        if (markers.length < 1) throw new Error("Please add at least one delivery point.");
        const capacity = Number(document.getElementById("capacity-input").value);
        const vehicleInput = document.getElementById("vehicle-count-input").value;
        const vehicleCount = vehicleInput === "" ? undefined : Number(vehicleInput);
        if (!Number.isInteger(capacity) || capacity <= 0) throw new Error("Capacity must be a positive integer.");
        if (vehicleCount !== undefined && (!Number.isInteger(vehicleCount) || vehicleCount <= 0)) throw new Error("Vehicle count must be a positive integer.");
        const demands = markers.map(marker => Number(marker.routeOptDemand));
        if (demands.some(demand => !Number.isInteger(demand) || demand <= 0 || demand > capacity)) throw new Error("Every demand must be a positive integer no greater than capacity.");
        if (vehicleCount !== undefined && demands.reduce((sum, demand) => sum + demand, 0) > capacity * vehicleCount) throw new Error("Total demand exceeds available vehicle capacity.");
        const depot = depotMarker.getLatLng();
        return {
            mode: "cvrp",
            depot: [depot.lat, depot.lng],
            points: markers.map(marker => {
                const position = marker.getLatLng();
                return [position.lat, position.lng];
            }),
            demands,
            capacity,
            ...(vehicleCount === undefined ? {} : { vehicle_count: vehicleCount }),
            algorithm: algorithmSelect.value
        };
    }

    async function optimize() {
        const cvrp = modeSelect.value === "cvrp";
        const markers = window.routeOptMarkers || [];
        if (!cvrp && markers.length < 2) throw new Error("Please add at least 2 delivery points.");
        const payload = cvrp ? buildCvrpPayload() : {
            points: markers.map(marker => {
                const position = marker.getLatLng();
                return [position.lat, position.lng];
            }),
            algorithm: algorithmSelect.value
        };
        const response = await fetch("http://127.0.0.1:5000/api/optimize", {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Unable to optimize route.");
        if (cvrp) {
            drawRoutes(data.route_details);
            totalDistance.innerHTML = Number(data.road_distance_km).toFixed(3) + " <small>km</small>";
            document.getElementById("route-duration").textContent = Number(data.total_route_duration_minutes).toFixed(1) + " phút";
            improvementDisplay.textContent = Number(data.comparison[data.algorithm]?.improvement ?? 0).toFixed(2) + "%";
            displayComparison(data.comparison, true);
        } else {
            drawRoute(data.route_geometry);
            totalDistance.innerHTML = Number(data.road_distance ?? data.total_distance).toFixed(3) + " <small>km</small>";
            document.getElementById("route-duration").textContent = Number(data.duration_minutes).toFixed(1) + " phút";
            improvementDisplay.textContent = Number(data.improvement).toFixed(2) + "%";
            displayComparison(data.comparison);
        }
        showStatus(`Đã tối ưu thành công bằng ${algorithmNames[data.algorithm] || data.algorithm}.`, "success");
    }

    modeSelect.addEventListener("change", updateModeControls);
    optimizeButton.addEventListener("click", async () => {
        optimizeButton.disabled = true;
        showStatus("Đang tính toán lộ trình đường bộ...", "info");
        try { await optimize(); } catch (error) { console.error(error); showStatus(error.message, "error"); }
        finally { optimizeButton.disabled = false; }
    });

    document.getElementById("clear-markers-btn").addEventListener("click", () => {
        clearRoutes();
        comparisonBody.innerHTML = '<tr><td colspan="4" class="empty-table">No comparison data available yet.</td></tr>';
        showStatus("Đã xóa lộ trình.", "info");
    });

    updateModeControls();
});
