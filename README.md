# RouteOpt

RouteOpt cung cấp hai luồng tối ưu tuyến:

- **TSP legacy**: một xe, tọa độ `[latitude, longitude]`, khoảng cách Haversine/OSRM.
- **CVRP**: nhiều xe, depot, demand và capacity; solver trả nhiều route đóng tại depot.

## Cài đặt

Yêu cầu Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI TSP legacy

```bash
python3 main.py --json --algorithm two_opt
python3 main.py --input points.json --algorithm all --json
```

Schema legacy:

```json
{
  "points": [[16.0471, 108.2068], [16.06, 108.22]],
  "depot": 0
}
```

## CLI CVRP

CVRP file dùng tọa độ phẳng `x/y`, không phải latitude/longitude. Depot luôn là node đầu tiên.

```bash
python3 data/duannhom.py --mssv 123456 --customers 20 --output data/instance.json
python3 main.py --cvrp-input data/instance.json --cvrp-algorithm all
```

Schema CVRP:

```json
{
  "name": "example",
  "depot_index": 0,
  "capacity": 10,
  "nodes": [
    {"id": 0, "x": 50, "y": 50, "demand": 0},
    {"id": 1, "x": 12, "y": 20, "demand": 4}
  ]
}
```

Kết quả CVRP gồm `routes`, `loads` và `distance`. Giá trị route là positional index trong mảng `nodes`; `node_ids` được trả riêng trong envelope CLI.

## Backend và giao diện

Terminal 1:

```bash
python3 backend/app.py
```

Terminal 2:

```bash
python3 -m http.server 8000 --directory frontend
```

Mở `http://127.0.0.1:8000`. Backend cần Internet để gọi OSRM public service.

Trong giao diện:

1. Chọn `CVRP (multiple vehicles)`.
2. Chọn `Set depot` rồi click một vị trí trên bản đồ.
3. Chọn `Add delivery`, click các khách hàng và chỉnh demand.
4. Nhập capacity, số xe tùy chọn và chạy tối ưu.

API CVRP nhận:

```json
{
  "mode": "cvrp",
  "depot": [16.0471, 108.2068],
  "points": [[16.06, 108.22], [16.08, 108.24]],
  "demands": [3, 4],
  "capacity": 5,
  "vehicle_count": 2,
  "algorithm": "nearest_neighbor"
}
```

API TSP cũ vẫn nhận `{ "points": [...], "algorithm": "two_opt" }` và giữ response legacy.

## Kiểm thử

```bash
python3 -m pytest -q
python3 -m py_compile main.py backend/app.py data/duannhom.py algorithms/*_cvrp.py
node --check frontend/js/map.js
node --check frontend/js/dashboard.js
node --check frontend/js/app.js
```

API tests mock OSRM, vì vậy test tự động không phụ thuộc mạng bên ngoài.
