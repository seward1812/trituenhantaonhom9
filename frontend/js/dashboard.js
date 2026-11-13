
document.addEventListener("DOMContentLoaded", function () {
    const optimizeButton = document.getElementById("optimize-btn");
    const algorithmSelect = document.getElementById("algorithm-select");
    const statusMessage = document.getElementById("status-message");

    const totalDistance = document.getElementById("total-distance");
    const improvementDisplay = document.getElementById("improvement");
    const comparisonBody = document.getElementById("comparison-body");

    const algorithmNames = {
        nearest_neighbor: "Nearest Neighbor",
        two_opt: "2-opt",
        nearest_insertion: "Nearest Insertion",
        farthest_insertion: "Farthest Insertion"
    };

    let routeLine = null;

    function showStatus(message, type = "info") {
        statusMessage.textContent = message;
        statusMessage.dataset.type = type;
    }

    // Hiển thị bảng so sánh thuật toán
    function displayComparison(comparison) {
        comparisonBody.innerHTML = "";

        if (!comparison) {
            comparisonBody.innerHTML =
                '<tr><td colspan="4">No comparison data available.</td></tr>';
            return;
        }

        Object.entries(comparison).forEach(([algorithm, result]) => {
            const row = document.createElement("tr");

            const name = algorithmNames[algorithm] || algorithm;
            const distance = Number(result.distance ?? result.total_distance ?? 0);
            const improvement = Number(result.improvement ?? 0);

            row.innerHTML = `
                <td>${name}</td>
                <td>${distance.toFixed(3)} km</td>
                <td>${improvement.toFixed(2)}%</td>
                <td>${result.route ? result.route.length : "-"}</td>
            `;

            comparisonBody.appendChild(row);
        });
    }

    // Vẽ tuyến đường thực tế do OSRM trả về
    function drawRoute(routeGeometry) {
        const map = window.routeOptMap;

        if (!map) {
            throw new Error("Không tìm thấy bản đồ.");
        }

        if (!Array.isArray(routeGeometry) || routeGeometry.length < 2) {
            throw new Error("OSRM không trả về hình dạng tuyến đường hợp lệ.");
        }

        if (routeLine) {
            map.removeLayer(routeLine);
            routeLine = null;
        }

        // GeoJSON OSRM trả về [longitude, latitude].
        // Leaflet cần [latitude, longitude].
        const latLngs = routeGeometry.map(function (coordinate) {
            const lng = Number(coordinate[0]);
            const lat = Number(coordinate[1]);

            if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                throw new Error("Tọa độ tuyến đường không hợp lệ.");
            }

            return [lat, lng];
        });

        routeLine = L.polyline(latLngs, {
            color: "#38bdf8",
            weight: 5,
            opacity: 0.95,
            lineJoin: "round"
        }).addTo(map);

        window.routeOptRouteLine = routeLine;

        map.fitBounds(routeLine.getBounds(), {
            padding: [40, 40]
        });
    }

    // Nút tối ưu lộ trình
    optimizeButton.addEventListener("click", async function () {
        const markers = window.routeOptMarkers || [];

        if (markers.length < 2) {
            showStatus("Vui lòng thêm ít nhất 2 điểm giao hàng.", "error");
            return;
        }

        optimizeButton.disabled = true;
        showStatus("Đang tính toán lộ trình đường bộ...", "info");

        try {
            // Lấy tọa độ các điểm trên bản đồ
            const points = markers.map(function (marker) {
                const position = marker.getLatLng();

                return [
                    position.lat,
                    position.lng
                ];
            });

            const algorithm = algorithmSelect.value;

            const response = await fetch("http://127.0.0.1:5000/api/optimize", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    points: points,
                    algorithm: algorithm
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || "Không thể tối ưu lộ trình.");
            }

            // Quan trọng: sử dụng route_geometry, không dùng data.route
            // để vẽ đường nối thẳng giữa các marker.
            drawRoute(data.route_geometry);

            // Hiển thị tổng khoảng cách
            totalDistance.innerHTML =
                Number(data.road_distance ?? data.total_distance).toFixed(3) +
                " <small>km</small>";

            // Hiển thị thời gian dự kiến nếu backend có trả về
            const duration = document.getElementById("route-duration");

            if (duration && data.duration_minutes !== undefined) {
                duration.textContent =
                    Number(data.duration_minutes).toFixed(1) + " phút";
            }

            // Hiển thị mức cải thiện
            improvementDisplay.textContent =
                Number(data.improvement).toFixed(2) + "%";

            // Hiển thị thuật toán được chọn
            displayComparison(data.comparison);

            const selectedName =
                algorithmNames[algorithm] || algorithm;

            showStatus(
                "Đã tối ưu thành công bằng " + selectedName + ".",
                "success"
            );

        } catch (error) {
            console.error("RouteOpt error:", error);
            showStatus(error.message, "error");

        } finally {
            optimizeButton.disabled = false;
        }
    });

    // Nút xóa các điểm giao hàng
    const clearButton = document.getElementById("clear-markers-btn");

    if (clearButton) {
        clearButton.addEventListener("click", function () {
            if (routeLine && window.routeOptMap) {
                window.routeOptMap.removeLayer(routeLine);
                routeLine = null;
                window.routeOptRouteLine = null;
            }

            comparisonBody.innerHTML =
                '<tr><td colspan="4" class="empty-table">' +
                'No comparison data available yet.' +
                '</td></tr>';

            showStatus("Đã xóa lộ trình.", "info");
        });
    }

    console.log("RouteOpt Dashboard loaded successfully!");
});
