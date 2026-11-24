
from distance import (
    create_distance_matrix,
    calculate_route_distance
)

from nearest_neighbor import nearest_neighbor
from two_opt import two_opt


# Danh sach toa do GPS
# Diem 0 la kho hang
locations = [
    (10.7769, 106.7009),
    (10.7800, 106.7009),
    (10.7769, 106.7100),
    (10.7850, 106.7150),
    (10.7900, 106.7050)
]


# Tao ma tran khoang cach
matrix = create_distance_matrix(locations)


# Chay Nearest Neighbor
route_nn = nearest_neighbor(matrix, depot=0)


# Cai thien bang 2-opt
route_2opt = two_opt(route_nn, matrix)


# Tinh tong khoang cach
distance_nn = calculate_route_distance(route_nn, matrix)

distance_2opt = calculate_route_distance(route_2opt, matrix)


# In ket qua
print("========== KET QUA KIEM THU ==========")

print("\nNearest Neighbor:")
print("Lo trinh:", route_nn)
print("Khoang cach: {:.3f} km".format(distance_nn))

print("\nNearest Neighbor + 2-opt:")
print("Lo trinh:", route_2opt)
print("Khoang cach: {:.3f} km".format(distance_2opt))

print("\n========== SO SANH ==========")

improvement = distance_nn - distance_2opt

print("Quang duong tiet kiem: {:.3f} km".format(improvement))

if distance_nn > 0:
    percentage = improvement / distance_nn * 100
    print("Ty le cai thien: {:.2f}%".format(percentage))

if distance_2opt <= distance_nn:
    print("Ket qua: 2-opt khong lam tang quang duong.")
else:
    print("Ket qua: Can kiem tra lai thuat toan.")
