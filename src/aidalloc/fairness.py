"""Fairness, coverage, and neglect-risk audits."""

from __future__ import annotations

import numpy as np
import pandas as pd


def coverage_table(regions: pd.DataFrame, needs: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    """Return region and country coverage table."""
    total_need = needs.groupby("region_id", as_index=False).agg(requested_units=("requested_units", "sum"), minimum_service_units=("minimum_service_units", "sum"))
    if allocation.empty:
        delivered = pd.DataFrame({"region_id": total_need["region_id"], "allocated_units": 0})
    else:
        delivered = allocation.groupby("region_id", as_index=False)["allocated_units"].sum()
    out = regions.merge(total_need, on="region_id", how="left").merge(delivered, on="region_id", how="left")
    out["allocated_units"] = out["allocated_units"].fillna(0).astype(int)
    out["coverage_ratio"] = np.where(out["requested_units"] > 0, out["allocated_units"] / out["requested_units"], 0.0)
    out["vulnerability_weighted_coverage"] = out["coverage_ratio"] / (0.5 + out["vulnerability_index"])
    out["minimum_service_met"] = out["allocated_units"] >= out["minimum_service_units"]
    out["region_neglect_risk"] = ((out["coverage_ratio"] < 0.35) & (out["vulnerability_index"] > 0.55)).astype(int)
    return out.sort_values("coverage_ratio").reset_index(drop=True)


def fairness_audit(regions: pd.DataFrame, needs: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    """Compute country-level and region-level fairness indicators."""
    coverage = coverage_table(regions, needs, allocation)
    country = coverage.groupby("country").agg(
        country_requested_units=("requested_units", "sum"),
        country_allocated_units=("allocated_units", "sum"),
        mean_region_coverage=("coverage_ratio", "mean"),
        min_region_coverage=("coverage_ratio", "min"),
        mean_vulnerability_weighted_coverage=("vulnerability_weighted_coverage", "mean"),
        region_neglect_risk=("region_neglect_risk", "mean"),
        minimum_service_violation_rate=("minimum_service_met", lambda x: float((~x).mean())),
    ).reset_index()
    country["country_coverage_ratio"] = np.where(
        country["country_requested_units"] > 0,
        country["country_allocated_units"] / country["country_requested_units"],
        0.0,
    )
    gap = float(country["country_coverage_ratio"].max() - country["country_coverage_ratio"].min()) if len(country) else 0.0
    disparity = float(coverage["coverage_ratio"].std(ddof=0)) if len(coverage) else 0.0
    country["country_coverage_gap"] = gap
    country["allocation_disparity_index"] = disparity
    return country.sort_values("country").reset_index(drop=True)


def aid_type_coverage(needs: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    """Coverage by aid type."""
    requested = needs.groupby("aid_type", as_index=False)["requested_units"].sum()
    if allocation.empty:
        delivered = pd.DataFrame({"aid_type": requested["aid_type"], "allocated_units": 0})
    else:
        delivered = allocation.groupby("aid_type", as_index=False)["allocated_units"].sum()
    out = requested.merge(delivered, on="aid_type", how="left")
    out["allocated_units"] = out["allocated_units"].fillna(0).astype(int)
    out["coverage_ratio"] = np.where(out["requested_units"] > 0, out["allocated_units"] / out["requested_units"], 0.0)
    return out.sort_values("coverage_ratio").reset_index(drop=True)


def summary_metrics(regions: pd.DataFrame, needs: pd.DataFrame, allocation: pd.DataFrame, fairness: pd.DataFrame) -> dict[str, float | int | str]:
    """Compact run summary for JSON and audit logs."""
    coverage = coverage_table(regions, needs, allocation)
    return {
        "region_count": int(len(regions)),
        "aid_type_count": int(needs["aid_type"].nunique()),
        "total_requested_units": int(needs["requested_units"].sum()),
        "total_allocated_units": int(allocation["allocated_units"].sum()) if not allocation.empty else 0,
        "mean_region_coverage": float(coverage["coverage_ratio"].mean()) if len(coverage) else 0.0,
        "minimum_service_violation_rate": float((~coverage["minimum_service_met"]).mean()) if len(coverage) else 0.0,
        "region_neglect_risk_rate": float(coverage["region_neglect_risk"].mean()) if len(coverage) else 0.0,
        "country_coverage_gap": float(fairness["country_coverage_gap"].iloc[0]) if len(fairness) else 0.0,
        "allocation_disparity_index": float(fairness["allocation_disparity_index"].iloc[0]) if len(fairness) else 0.0,
    }
