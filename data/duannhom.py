"""Data utilities for Capacitated Vehicle Routing Problem (CVRP)."""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CVRPInstance:
    """A CVRP instance with the depot stored at index 0."""

    name: str
    node_ids: list[int]
    coordinates: list[tuple[float, float]]
    demands: list[int]
    capacity: int

    def __post_init__(self) -> None:
        size = len(self.node_ids)
        if size == 0 or len(self.coordinates) != size or len(self.demands) != size:
            raise ValueError("Node IDs, coordinates, and demands must have equal non-zero lengths.")
        if len(set(self.node_ids)) != size:
            raise ValueError("Node IDs must be unique.")
        if self.demands[0] != 0:
            raise ValueError("The depot (index 0) must have demand 0.")
        if self.capacity <= 0:
            raise ValueError("Vehicle capacity must be positive.")
        if any(demand <= 0 or demand > self.capacity for demand in self.demands[1:]):
            raise ValueError("Each customer demand must be between 1 and vehicle capacity.")
        if any(not math.isfinite(value) for point in self.coordinates for value in point):
            raise ValueError("Coordinates must be finite numbers.")

    def distance_matrix(self) -> list[list[float]]:
        """Return the symmetric Euclidean distance matrix."""
        return [
            [
                math.hypot(x1 - x2, y1 - y2)
                for x2, y2 in self.coordinates
            ]
            for x1, y1 in self.coordinates
        ]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "depot_index": 0,
            "capacity": self.capacity,
            "nodes": [
                {
                    "id": node_id,
                    "x": x,
                    "y": y,
                    "demand": demand,
                }
                for node_id, (x, y), demand in zip(
                    self.node_ids, self.coordinates, self.demands
                )
            ],
        }


def generate_instance(mssv: str, customer_count: int = 20) -> CVRPInstance:
    """Generate repeatable customer locations and demands using an MSSV as seed."""
    digits = re.sub(r"\D", "", mssv)
    if not digits:
        raise ValueError("MSSV must contain at least one digit.")
    if customer_count < 1:
        raise ValueError("Customer count must be at least 1.")
    if customer_count > 10_000:
        raise ValueError("Customer count cannot exceed 10,000.")

    rng = random.Random(int(digits))
    depot = (50, 50)
    used_locations = {depot}
    customers: list[tuple[int, int]] = []
    while len(customers) < customer_count:
        location = (rng.randint(0, 100), rng.randint(0, 100))
        if location not in used_locations:
            customers.append(location)
            used_locations.add(location)

    customer_demands = [rng.randint(1, 10) for _ in range(customer_count)]
    capacity = max(max(customer_demands), math.ceil(sum(customer_demands) / 4))
    return CVRPInstance(
        name=f"synthetic_mssv_{digits}",
        node_ids=list(range(customer_count + 1)),
        coordinates=[depot, *customers],
        demands=[0, *customer_demands],
        capacity=capacity,
    )


def load_cvrplib(path: str | Path) -> CVRPInstance:
    """Load a CVRPLIB instance with NODE_COORD_SECTION and EUC_2D distances."""
    source = Path(path)
    headers: dict[str, str] = {}
    coordinates: dict[int, tuple[float, float]] = {}
    demands: dict[int, int] = {}
    depot_ids: list[int] = []
    section = ""

    with source.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            marker = line.upper()
            if marker in {
                "NODE_COORD_SECTION",
                "DEMAND_SECTION",
                "DEPOT_SECTION",
                "EOF",
            }:
                section = "" if marker == "EOF" else marker
                continue

            if not section:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().upper()] = value.strip()
                continue

            fields = line.split()
            try:
                if section == "NODE_COORD_SECTION":
                    if len(fields) < 3:
                        raise ValueError("expected node ID, x, and y")
                    node_id = int(fields[0])
                    coordinates[node_id] = (float(fields[1]), float(fields[2]))
                elif section == "DEMAND_SECTION":
                    if len(fields) < 2:
                        raise ValueError("expected node ID and demand")
                    demands[int(fields[0])] = int(fields[1])
                elif section == "DEPOT_SECTION":
                    node_id = int(fields[0])
                    if node_id != -1:
                        depot_ids.append(node_id)
            except ValueError as error:
                raise ValueError(
                    f"Invalid CVRPLIB data at {source}:{line_number}: {error}"
                ) from error

    if headers.get("EDGE_WEIGHT_TYPE", "EUC_2D").upper() != "EUC_2D":
        raise ValueError("Only CVRPLIB EDGE_WEIGHT_TYPE EUC_2D is supported.")
    if not coordinates or set(coordinates) != set(demands):
        raise ValueError("CVRPLIB file must have matching, non-empty coordinate and demand sections.")
    if len(depot_ids) != 1 or depot_ids[0] not in coordinates:
        raise ValueError("CVRPLIB file must define exactly one valid depot.")
    try:
        capacity = int(headers["CAPACITY"])
    except (KeyError, ValueError) as error:
        raise ValueError("CVRPLIB file must define a numeric CAPACITY.") from error

    depot_id = depot_ids[0]
    ordered_ids = [depot_id, *sorted(node_id for node_id in coordinates if node_id != depot_id)]
    return CVRPInstance(
        name=headers.get("NAME", source.stem),
        node_ids=ordered_ids,
        coordinates=[coordinates[node_id] for node_id in ordered_ids],
        demands=[demands[node_id] for node_id in ordered_ids],
        capacity=capacity,
    )


def save_json(instance: CVRPInstance, output_path: str | Path) -> None:
    """Save an instance in the shared JSON format used by the project."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(instance.to_dict(), file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or normalize CVRP data.")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--mssv", help="Generate deterministic data from an MSSV.")
    sources.add_argument("--cvrplib", help="Path to a CVRPLIB EUC_2D instance.")
    parser.add_argument("--customers", type=int, default=20, help="Number of generated customers.")
    parser.add_argument("--output", type=Path, required=True, help="Path for normalized JSON output.")
    args = parser.parse_args()

    instance = (
        generate_instance(args.mssv, args.customers)
        if args.mssv is not None
        else load_cvrplib(args.cvrplib)
    )
    save_json(instance, args.output)
    print(
        f"Saved {instance.name}: {len(instance.demands) - 1} customers, "
        f"capacity {instance.capacity} -> {args.output}"
    )


if __name__ == "__main__":
    main()