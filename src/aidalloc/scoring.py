"""Need, urgency, and fairness scoring functions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def score_needs(regions: pd.DataFrame, needs: pd.DataFrame) -> pd.DataFrame:
    """Attach transparent severity, urgency, and vulnerability scores to needs."""
    frame = needs.merge(regions, on="region_id", how="left")
    requested = frame["requested_units"].astype(float)
    frame["normalized_need"] = requested / max(float(requested.max()), 1.0)
    frame["urgency_score"] = np.clip(
        0.35 * frame["normalized_need"]
        + 0.25 * frame["vulnerability_index"]
        + 0.25 * frame["infrastructure_damage"]
        + 0.15 * (1.0 / np.sqrt(frame["days_since_event"].clip(lower=1))),
        0,
        1,
    )
    frame["vulnerability_weight"] = np.clip(0.55 + frame["vulnerability_index"] + 0.25 * frame["access_constraint"], 0.25, 1.85)
    frame["need_priority_score"] = np.clip(
        0.45 * frame["urgency_score"]
        + 0.35 * frame["vulnerability_index"]
        + 0.20 * frame["access_constraint"],
        0,
        1,
    )
    return frame


def logistics_access_score(routes: pd.DataFrame) -> pd.DataFrame:
    """Compute accessible-route score from travel delay and route risk."""
    out = routes.copy()
    max_hours = max(float(out["estimated_travel_hours"].max()), 1.0)
    out["delay_score"] = 1.0 - out["estimated_travel_hours"] / max_hours
    out["logistics_access_score"] = np.clip(0.65 * out["delay_score"] + 0.35 * (1.0 - out["route_risk"]), 0, 1)
    return out


def country_fairness_boost(allocation: pd.DataFrame, scored_needs: pd.DataFrame) -> dict[str, float]:
    """Return country boost values for currently under-covered countries."""
    if allocation.empty:
        countries = scored_needs["country"].unique().tolist()
        return {country: 0.10 for country in countries}
    need_by_country = scored_needs.groupby("country")["requested_units"].sum()
    alloc_by_country = allocation.groupby("country")["allocated_units"].sum()
    coverage = (alloc_by_country / need_by_country).fillna(0.0)
    target = float(coverage.max()) if not coverage.empty else 0.0
    boosts = {}
    for country in need_by_country.index:
        gap = max(0.0, target - float(coverage.get(country, 0.0)))
        boosts[country] = min(0.35, 0.10 + gap)
    return boosts
