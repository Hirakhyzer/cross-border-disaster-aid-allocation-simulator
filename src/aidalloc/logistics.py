"""Logistics and route-selection utilities."""

from __future__ import annotations

import pandas as pd

from aidalloc.scoring import logistics_access_score


def best_routes(routes: pd.DataFrame) -> pd.DataFrame:
    """Select best available route per region and warehouse using transparent logistics score."""
    scored = logistics_access_score(routes)
    return scored.sort_values(["region_id", "logistics_access_score"], ascending=[True, False]).reset_index(drop=True)


def route_summary(routes: pd.DataFrame) -> pd.DataFrame:
    """Summarize synthetic logistics constraints by domestic/cross-border category."""
    scored = logistics_access_score(routes)
    grouped = scored.groupby(["cross_border", "border_friction"], dropna=False).agg(
        route_count=("region_id", "count"),
        mean_distance_km=("distance_km", "mean"),
        mean_travel_hours=("estimated_travel_hours", "mean"),
        mean_route_risk=("route_risk", "mean"),
        mean_access_score=("logistics_access_score", "mean"),
    )
    return grouped.reset_index().sort_values(["cross_border", "border_friction"]).reset_index(drop=True)


def nearest_route_for_pair(routes: pd.DataFrame, warehouse_id: str, region_id: str) -> dict:
    """Return a single route record for an allocation pair."""
    match = routes.loc[(routes["warehouse_id"] == warehouse_id) & (routes["region_id"] == region_id)]
    if match.empty:
        raise ValueError(f"No route for warehouse={warehouse_id}, region={region_id}")
    return match.iloc[0].to_dict()
