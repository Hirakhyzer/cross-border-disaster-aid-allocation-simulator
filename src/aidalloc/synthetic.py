"""Deterministic synthetic cross-border humanitarian aid data.

All countries, regions, warehouses, actors, routes, stocks, and needs are
fictional. The data exists to test allocation logic, fairness metrics, logistics
constraints, and transparency reports without real crisis information.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

AID_TYPES = ["food_kits", "clean_water", "medical_kits", "shelter_kits", "hygiene_kits", "fuel", "generators", "mobile_clinics"]
COUNTRIES = ["Northland", "Eastoria", "Southport"]
DISASTER_TYPES = ["flood", "earthquake", "cyclone", "conflict_displacement"]
BORDER_FRICTION = ["low", "medium", "high"]


@dataclass(frozen=True)
class SyntheticAidConfig:
    regions: int = 24
    warehouses: int = 4
    seed: int = 42

    def __post_init__(self) -> None:
        if self.regions < 9:
            raise ValueError("Use at least 9 regions for cross-country fairness analysis.")
        if self.warehouses < 2:
            raise ValueError("Use at least 2 warehouses for logistics comparison.")


def generate_synthetic_aid_data(config: SyntheticAidConfig | None = None) -> dict[str, pd.DataFrame]:
    cfg = config or SyntheticAidConfig()
    rng = np.random.default_rng(cfg.seed)
    regions = _regions(cfg, rng)
    warehouses = _warehouses(cfg, rng)
    inventory = _inventory(warehouses, rng)
    needs = _needs(regions, rng)
    routes = _routes(regions, warehouses, rng)
    actors = _actors(rng)
    return {"regions": regions, "warehouses": warehouses, "inventory": inventory, "needs": needs, "routes": routes, "actors": actors}


def _regions(cfg: SyntheticAidConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx in range(cfg.regions):
        country = COUNTRIES[idx % len(COUNTRIES)]
        disaster = DISASTER_TYPES[idx % len(DISASTER_TYPES)]
        population = int(rng.integers(18_000, 180_000))
        affected_share = float(np.clip(rng.beta(2.4, 3.2), 0.08, 0.88))
        affected_population = int(population * affected_share)
        vulnerability = float(np.clip(rng.normal(0.45 + 0.08 * (idx % 3), 0.16), 0.05, 0.96))
        infrastructure_damage = float(np.clip(rng.beta(2.0, 2.6), 0.04, 0.95))
        access_constraint = float(np.clip(0.25 * infrastructure_damage + rng.normal(0.22, 0.10), 0.02, 0.90))
        days_since_event = int(rng.integers(1, 15))
        rows.append({
            "region_id": f"R-{idx+1:03d}",
            "country": country,
            "region_name": f"{country} District {idx+1:02d}",
            "disaster_type": disaster,
            "population": population,
            "affected_population": affected_population,
            "vulnerability_index": round(vulnerability, 3),
            "infrastructure_damage": round(infrastructure_damage, 3),
            "access_constraint": round(access_constraint, 3),
            "days_since_event": days_since_event,
            "latitude": round(22.0 + idx * 0.27 + float(rng.normal(0, 0.12)), 4),
            "longitude": round(62.0 + (idx % 9) * 0.45 + float(rng.normal(0, 0.12)), 4),
        })
    return pd.DataFrame(rows)


def _warehouses(cfg: SyntheticAidConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx in range(cfg.warehouses):
        country = COUNTRIES[idx % len(COUNTRIES)]
        rows.append({
            "warehouse_id": f"W-{idx+1:02d}",
            "country": country,
            "warehouse_name": f"{country} Humanitarian Hub {idx+1}",
            "daily_dispatch_capacity": int(rng.integers(900, 2400)),
            "handling_reliability": round(float(np.clip(rng.normal(0.82, 0.08), 0.55, 0.98)), 3),
            "latitude": round(21.7 + idx * 0.95 + float(rng.normal(0, 0.08)), 4),
            "longitude": round(61.7 + idx * 0.83 + float(rng.normal(0, 0.08)), 4),
        })
    return pd.DataFrame(rows)


def _inventory(warehouses: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for warehouse in warehouses.itertuples(index=False):
        for aid_type in AID_TYPES:
            base = rng.integers(350, 1700)
            difficulty = {"mobile_clinics": 0.35, "generators": 0.45, "fuel": 0.55}.get(aid_type, 1.0)
            stock = int(max(8, base * difficulty))
            rows.append({
                "warehouse_id": warehouse.warehouse_id,
                "aid_type": aid_type,
                "stock_units": stock,
                "unit_weight_kg": round(float(rng.uniform(1.5, 35.0)), 2),
                "handling_complexity": round(float(rng.uniform(0.15, 0.75)), 3),
            })
    return pd.DataFrame(rows)


def _needs(regions: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    multipliers = {
        "food_kits": 0.040,
        "clean_water": 0.065,
        "medical_kits": 0.018,
        "shelter_kits": 0.022,
        "hygiene_kits": 0.030,
        "fuel": 0.006,
        "generators": 0.0025,
        "mobile_clinics": 0.0008,
    }
    rows = []
    for region in regions.itertuples(index=False):
        for aid_type, multiplier in multipliers.items():
            disaster_boost = 1.0
            if region.disaster_type == "flood" and aid_type in {"clean_water", "hygiene_kits", "shelter_kits"}:
                disaster_boost = 1.35
            if region.disaster_type == "earthquake" and aid_type in {"medical_kits", "shelter_kits", "generators"}:
                disaster_boost = 1.30
            if region.disaster_type == "cyclone" and aid_type in {"food_kits", "clean_water", "fuel"}:
                disaster_boost = 1.22
            if region.disaster_type == "conflict_displacement" and aid_type in {"food_kits", "medical_kits", "mobile_clinics"}:
                disaster_boost = 1.30
            requested = int(max(1, region.affected_population * multiplier * disaster_boost * rng.uniform(0.80, 1.25)))
            rows.append({
                "region_id": region.region_id,
                "aid_type": aid_type,
                "requested_units": requested,
                "minimum_service_units": int(max(1, requested * 0.28)),
            })
    return pd.DataFrame(rows)


def _routes(regions: pd.DataFrame, warehouses: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for warehouse in warehouses.itertuples(index=False):
        for region in regions.itertuples(index=False):
            cross_border = int(warehouse.country != region.country)
            friction = str(rng.choice(BORDER_FRICTION, p=[0.38, 0.42, 0.20])) if cross_border else "domestic"
            distance = float(np.sqrt((warehouse.latitude - region.latitude) ** 2 + (warehouse.longitude - region.longitude) ** 2) * 95 + rng.uniform(35, 210))
            border_delay = {"domestic": 0.0, "low": 5.0, "medium": 16.0, "high": 34.0}[friction]
            route_risk = float(np.clip(0.18 + 0.55 * region.infrastructure_damage + 0.25 * region.access_constraint + rng.normal(0, 0.08), 0.02, 0.98))
            damaged_infrastructure_delay = 9.0 * route_risk
            travel_hours = distance / rng.uniform(34, 58) + border_delay + damaged_infrastructure_delay
            rows.append({
                "warehouse_id": warehouse.warehouse_id,
                "region_id": region.region_id,
                "cross_border": cross_border,
                "border_friction": friction,
                "distance_km": round(distance, 2),
                "route_risk": round(route_risk, 3),
                "border_delay_hours": round(border_delay, 2),
                "estimated_travel_hours": round(float(travel_hours), 2),
            })
    return pd.DataFrame(rows)


def _actors(rng: np.random.Generator) -> pd.DataFrame:
    names = ["ReliefBridge", "WaterReach", "HealthFirst", "ShelterLink", "FoodRoute"]
    return pd.DataFrame({
        "actor_id": [f"NGO-{i+1:02d}" for i in range(len(names))],
        "actor_name": names,
        "coordination_role": ["logistics", "water", "medical", "shelter", "food"],
        "data_origin": ["synthetic fictional partner" for _ in names],
    })
