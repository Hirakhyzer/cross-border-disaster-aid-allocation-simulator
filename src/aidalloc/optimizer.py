"""Transparent aid allocation policies.

The optimizer uses deterministic greedy allocation rather than hidden black-box
optimization. It is meant for research comparison and human review.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aidalloc.scoring import logistics_access_score, score_needs


def allocate_aid(
    regions: pd.DataFrame,
    needs: pd.DataFrame,
    inventory: pd.DataFrame,
    routes: pd.DataFrame,
    policy: str = "fairness_aware",
    min_service_target: float = 0.28,
) -> pd.DataFrame:
    """Allocate stock to region needs under a transparent policy.

    Parameters
    ----------
    policy:
        ``urgency_first`` or ``fairness_aware``.
    """
    if policy not in {"urgency_first", "fairness_aware"}:
        raise ValueError("policy must be urgency_first or fairness_aware")

    scored = score_needs(regions, needs)
    route_scores = logistics_access_score(routes)
    remaining_stock = inventory.set_index(["warehouse_id", "aid_type"])["stock_units"].astype(float).to_dict()
    remaining_need = needs.set_index(["region_id", "aid_type"])["requested_units"].astype(float).to_dict()
    allocation_rows: list[dict] = []
    country_delivered = {country: 0.0 for country in regions["country"].unique()}
    country_need = scored.groupby("country")["requested_units"].sum().to_dict()

    candidates = []
    for need in scored.itertuples(index=False):
        pair_routes = route_scores.loc[route_scores["region_id"] == need.region_id].sort_values("logistics_access_score", ascending=False)
        for route in pair_routes.itertuples(index=False):
            stock = remaining_stock.get((route.warehouse_id, need.aid_type), 0.0)
            if stock <= 0:
                continue
            candidates.append({
                "region_id": need.region_id,
                "country": need.country,
                "aid_type": need.aid_type,
                "requested_units": float(need.requested_units),
                "minimum_service_units": float(need.minimum_service_units),
                "warehouse_id": route.warehouse_id,
                "estimated_travel_hours": float(route.estimated_travel_hours),
                "route_risk": float(route.route_risk),
                "cross_border": int(route.cross_border),
                "border_friction": route.border_friction,
                "logistics_access_score": float(route.logistics_access_score),
                "need_priority_score": float(need.need_priority_score),
                "vulnerability_index": float(need.vulnerability_index),
                "urgency_score": float(need.urgency_score),
            })
    candidate_frame = pd.DataFrame(candidates)
    if candidate_frame.empty:
        return pd.DataFrame(columns=_allocation_columns())

    rounds = 3 if policy == "fairness_aware" else 2
    for round_idx in range(rounds):
        candidate_frame = candidate_frame.copy()
        if policy == "fairness_aware":
            coverage = {
                country: country_delivered.get(country, 0.0) / max(country_need.get(country, 1.0), 1.0)
                for country in country_need
            }
            max_coverage = max(coverage.values()) if coverage else 0.0
            candidate_frame["fairness_boost"] = candidate_frame["country"].map(lambda c: min(0.40, max(0.08, max_coverage - coverage.get(c, 0.0) + 0.08)))
            candidate_frame["minimum_service_boost"] = candidate_frame.apply(
                lambda row: _minimum_service_boost(allocation_rows, row["region_id"], row["aid_type"], row["minimum_service_units"]),
                axis=1,
            )
        else:
            candidate_frame["fairness_boost"] = 0.0
            candidate_frame["minimum_service_boost"] = 0.0
        candidate_frame["allocation_score"] = (
            0.36 * candidate_frame["need_priority_score"]
            + 0.22 * candidate_frame["urgency_score"]
            + 0.18 * candidate_frame["vulnerability_index"]
            + 0.14 * candidate_frame["logistics_access_score"]
            + 0.10 * candidate_frame["minimum_service_boost"]
            + candidate_frame["fairness_boost"]
        )
        ordered = candidate_frame.sort_values("allocation_score", ascending=False)
        for row in ordered.itertuples(index=False):
            key_need = (row.region_id, row.aid_type)
            key_stock = (row.warehouse_id, row.aid_type)
            need_left = remaining_need.get(key_need, 0.0)
            stock_left = remaining_stock.get(key_stock, 0.0)
            if need_left <= 0 or stock_left <= 0:
                continue
            target = row.minimum_service_units if policy == "fairness_aware" and round_idx == 0 else row.requested_units
            needed_to_target = max(0.0, min(need_left, target - _allocated_so_far(allocation_rows, row.region_id, row.aid_type)))
            if needed_to_target <= 0:
                needed_to_target = need_left
            batch = max(1.0, min(stock_left, needed_to_target, max(4.0, row.requested_units * 0.33)))
            if batch <= 0:
                continue
            remaining_stock[key_stock] = stock_left - batch
            remaining_need[key_need] = need_left - batch
            country_delivered[row.country] += batch
            allocation_rows.append({
                "policy": policy,
                "allocation_round": round_idx + 1,
                "region_id": row.region_id,
                "country": row.country,
                "aid_type": row.aid_type,
                "warehouse_id": row.warehouse_id,
                "allocated_units": int(round(batch)),
                "requested_units": int(round(row.requested_units)),
                "coverage_after_allocation": round(_coverage_after(allocation_rows, row.region_id, row.aid_type, batch, row.requested_units), 4),
                "estimated_travel_hours": round(row.estimated_travel_hours, 2),
                "route_risk": round(row.route_risk, 3),
                "cross_border": int(row.cross_border),
                "border_friction": row.border_friction,
                "need_priority_score": round(row.need_priority_score, 4),
                "allocation_score": round(float(row.allocation_score), 4),
                "decision_rationale": _rationale(policy, row),
            })
    return pd.DataFrame(allocation_rows, columns=_allocation_columns())


def unmet_need_table(needs: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    """Compute unmet need by region and aid type."""
    delivered = allocation.groupby(["region_id", "aid_type"], as_index=False)["allocated_units"].sum() if not allocation.empty else pd.DataFrame(columns=["region_id", "aid_type", "allocated_units"])
    out = needs.merge(delivered, on=["region_id", "aid_type"], how="left")
    out["allocated_units"] = out["allocated_units"].fillna(0).astype(int)
    out["unmet_units"] = (out["requested_units"] - out["allocated_units"]).clip(lower=0).astype(int)
    out["coverage_ratio"] = np.where(out["requested_units"] > 0, out["allocated_units"] / out["requested_units"], 0.0)
    out["minimum_service_met"] = out["allocated_units"] >= out["minimum_service_units"]
    return out.sort_values(["coverage_ratio", "unmet_units"], ascending=[True, False]).reset_index(drop=True)


def compare_policies(regions: pd.DataFrame, needs: pd.DataFrame, inventory: pd.DataFrame, routes: pd.DataFrame) -> pd.DataFrame:
    """Run both policies and return compact comparison metrics."""
    from aidalloc.fairness import fairness_audit

    rows = []
    for policy in ["urgency_first", "fairness_aware"]:
        plan = allocate_aid(regions, needs, inventory, routes, policy=policy)
        unmet = unmet_need_table(needs, plan)
        audit = fairness_audit(regions, needs, plan)
        rows.append({
            "policy": policy,
            "allocated_units": int(plan["allocated_units"].sum()) if not plan.empty else 0,
            "mean_coverage": float(unmet["coverage_ratio"].mean()) if len(unmet) else 0.0,
            "minimum_service_violation_rate": float((~unmet["minimum_service_met"]).mean()) if len(unmet) else 0.0,
            "country_coverage_gap": float(audit["country_coverage_gap"].iloc[0]) if len(audit) else 0.0,
            "neglect_risk_rate": float(audit["region_neglect_risk"].mean()) if len(audit) else 0.0,
        })
    return pd.DataFrame(rows)


def _allocated_so_far(rows: list[dict], region_id: str, aid_type: str) -> float:
    return float(sum(row["allocated_units"] for row in rows if row["region_id"] == region_id and row["aid_type"] == aid_type))


def _coverage_after(rows: list[dict], region_id: str, aid_type: str, batch: float, requested: float) -> float:
    return min(1.0, (_allocated_so_far(rows, region_id, aid_type) + batch) / max(requested, 1.0))


def _minimum_service_boost(rows: list[dict], region_id: str, aid_type: str, minimum_service_units: float) -> float:
    return 1.0 if _allocated_so_far(rows, region_id, aid_type) < minimum_service_units else 0.0


def _rationale(policy: str, row) -> str:
    if policy == "fairness_aware":
        return "Need, urgency, vulnerability, route access, minimum-service target, and country coverage fairness boost considered."
    return "Need, urgency, vulnerability, and route access considered."


def _allocation_columns() -> list[str]:
    return [
        "policy", "allocation_round", "region_id", "country", "aid_type", "warehouse_id", "allocated_units",
        "requested_units", "coverage_after_allocation", "estimated_travel_hours", "route_risk", "cross_border",
        "border_friction", "need_priority_score", "allocation_score", "decision_rationale",
    ]
