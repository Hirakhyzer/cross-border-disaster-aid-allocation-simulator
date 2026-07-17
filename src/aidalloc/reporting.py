"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd


def write_report(
    path: str | Path,
    summary: dict[str, Any],
    allocation: pd.DataFrame,
    unmet: pd.DataFrame,
    fairness: pd.DataFrame,
    logistics: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    """Write an evidence-only synthetic allocation report."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Synthetic Cross-Border Disaster Aid Allocation Report",
        "",
        "> Synthetic research warning: this report uses fictional crisis data only. It is not an official humanitarian allocation plan, route instruction, or operational decision.",
        "",
        "## Summary",
        "",
        f"- Regions: `{summary['region_count']}`",
        f"- Aid types: `{summary['aid_type_count']}`",
        f"- Requested units: `{summary['total_requested_units']}`",
        f"- Allocated units: `{summary['total_allocated_units']}`",
        f"- Mean region coverage: `{summary['mean_region_coverage']:.3f}`",
        f"- Minimum service violation rate: `{summary['minimum_service_violation_rate']:.3f}`",
        f"- Region neglect-risk rate: `{summary['region_neglect_risk_rate']:.3f}`",
        f"- Country coverage gap: `{summary['country_coverage_gap']:.3f}`",
        "",
        "## Policy comparison",
        "",
        comparison.to_markdown(index=False),
        "",
        "## Top allocations",
        "",
        "| Region | Country | Aid type | Warehouse | Units | Travel hours | Score | Rationale |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in allocation.sort_values("allocation_score", ascending=False).head(12).itertuples(index=False):
        lines.append(
            f"| {row.region_id} | {row.country} | {row.aid_type} | {row.warehouse_id} | {row.allocated_units} | {row.estimated_travel_hours:.2f} | {row.allocation_score:.2f} | {row.decision_rationale} |"
        )
    lines.extend([
        "",
        "## Highest unmet need",
        "",
        "| Region | Aid type | Requested | Allocated | Unmet | Coverage | Minimum met |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ])
    for row in unmet.sort_values(["coverage_ratio", "unmet_units"], ascending=[True, False]).head(12).itertuples(index=False):
        lines.append(f"| {row.region_id} | {row.aid_type} | {row.requested_units} | {row.allocated_units} | {row.unmet_units} | {row.coverage_ratio:.2f} | {row.minimum_service_met} |")
    lines.extend([
        "",
        "## Fairness audit",
        "",
        fairness.to_markdown(index=False),
        "",
        "## Logistics summary",
        "",
        logistics.to_markdown(index=False),
        "",
        "## Humanitarian governance boundary",
        "",
        "The allocation score is a transparent research proxy. Real-world use requires field validation, local context, consent and privacy controls, humanitarian coordination, legal review, and accountable human decision-making.",
    ])
    destination.write_text("\n".join(lines), encoding="utf-8")
