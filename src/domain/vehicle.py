# src/domain/vehicle.py
from dataclasses import dataclass

@dataclass
class VehicleType:
    name: str
    count: int
    autonomy: float
    cost_per_km: float = 1.0

def default_fleet():
    return [
        VehicleType(name="Moto", count=5, autonomy=80.0, cost_per_km=1.0),
        VehicleType(name="Van",  count=2, autonomy=250.0, cost_per_km=1.4)
    ]
