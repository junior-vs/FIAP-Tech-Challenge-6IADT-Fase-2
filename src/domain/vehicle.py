# src/domain/vehicle.py
from dataclasses import dataclass

@dataclass
class VehicleType:
    name: str
    count: int
    autonomy: float
    cost_per_km: float = 1.0
    max_weight: float = 0.0  #Peso máximo em gramas
    max_volume: float = 0.0  #Volume máximo em cm³


def default_fleet():
    # Observação: 1000g = 1kg; 1.000.000 cm³ = 1m³
    
    # Restrição de Produto (para referência): Peso máximo = 10.000g (10kg)
    # Restrição de Produto (para referência): Dimensão max = 100cm
    
    return [
        VehicleType(
            name="Moto", 
            count=5, 
            autonomy=80.0, 
            cost_per_km=1.0,
            # Uma moto pequena suporta ~25 kg de carga total
            max_weight=25_000.0,
            # Um baú pequeno/mochila grande: 30x30x30 cm = 27.000 cm³
            max_volume=27_000.0 
        ),
        VehicleType(
            name="Van",  
            count=2, 
            autonomy=250.0, 
            cost_per_km=1.4,
            # Uma Van suporta facilmente 500 kg de carga
            max_weight=500_000.0, 
            # Espaço de carga: ~ 2m x 1m x 1m = 2.000.000 cm³
            max_volume=2_000_000.0
        )
    ]