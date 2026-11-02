# trituenhantaonhom9

Mục tiêu dự án
Xây dựng mô hình dữ liệu gồm kho hàng và các địa điểm giao hàng.
Tính toán khoảng cách giữa các địa điểm.
Xây dựng ma trận khoảng cách phục vụ quá trình tìm kiếm.
Nghiên cứu và áp dụng các thuật toán AI để tối ưu hóa lộ trình.
Đánh giá, so sánh hiệu quả giữa các thuật toán.
Trực quan hóa lộ trình để người dùng dễ dàng theo dõi kết quả.

1. Clone repository

git clone https://github.com/seward1812/trituenhantaonhom9.git
cd trituenhantaonhom9

2. Kiểm tra dữ liệu địa điểm

Dự án hiện sử dụng 7 địa điểm, bao gồm:

1 điểm xuất phát (Depot).

6 địa điểm giao hàng.

Dữ liệu được lưu trong data/locations.py.

3. Chạy thử chương trình tính khoảng cách

Mở Terminal tại thư mục gốc của dự án và chạy:

python -c "from data.locations import locations; from algorithms.distance import create_distance_matrix; print(create_distan

Chuẩn bị trước khi demo
Dự án: trituenhantaonhom9

Cấu trúc thư mục chính:
trituenhantaonhom9/
│
├── algorithms/
│   ├── distance.py
│   ├── nearest_neighbor.py
│   └── two_opt.py
│
├── data/
│   └── locations.py
│
├── evaluation/
│
├── visualization/
│
├── main.py
└── README.md

4. DEMO
Trong PowerShell, nhập:
cd .\trituenhantaonhom9-main
cd .\trituenhantaonhom9

Kiểm tra bạn đang ở đúng thư mục dự án chạy:
pwd

Kiểm tra cấu trúc thư mục:
tree /F

Chạy file main.py:
python main.py

Kiểm tra thuật toán Nearest Neighbor
python -c "from data.locations import locations; from algorithms.distance import create_distance_matrix; from algorithms.nearest_neighbor import nearest_neighbor; matrix = create_distance_matrix(locations); route = nearest_neighbor(matrix); total = sum(matrix[route[i]][route[i+1]] for i in range(len(route)-1)); print('LO TRINH:', route); print('TONG KHOANG CACH:', round(total, 2))"

Chạy toàn bộ chương trình
python main.py

