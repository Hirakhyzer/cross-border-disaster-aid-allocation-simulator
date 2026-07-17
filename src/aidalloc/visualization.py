"""Visualization utilities for the synthetic aid allocation lab."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def _save(path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(destination, dpi=180)
    plt.close()


def plot_need_urgency(scored_needs: pd.DataFrame, path: str | Path) -> None:
    top = scored_needs.sort_values("need_priority_score", ascending=False).head(15)
    labels = top["region_id"] + " / " + top["aid_type"]
    plt.figure(figsize=(11, 6))
    plt.barh(labels, top["need_priority_score"])
    plt.gca().invert_yaxis()
    plt.xlabel("Need priority score")
    plt.title("Highest synthetic regional aid priorities")
    _save(path)


def plot_allocation_coverage(coverage: pd.DataFrame, path: str | Path) -> None:
    ordered = coverage.sort_values("coverage_ratio")
    plt.figure(figsize=(11, 6))
    plt.bar(ordered["region_id"], ordered["coverage_ratio"])
    plt.xticks(rotation=70, ha="right")
    plt.ylabel("Coverage ratio")
    plt.title("Allocation coverage by region")
    _save(path)


def plot_fairness_gaps(fairness: pd.DataFrame, path: str | Path) -> None:
    plt.figure(figsize=(9, 5))
    plt.bar(fairness["country"], fairness["country_coverage_ratio"])
    plt.ylabel("Country coverage ratio")
    plt.title("Cross-border allocation coverage by country")
    _save(path)


def plot_logistics_delay(routes: pd.DataFrame, path: str | Path) -> None:
    summary = routes.groupby("border_friction", as_index=False)["estimated_travel_hours"].mean().sort_values("estimated_travel_hours")
    plt.figure(figsize=(9, 5))
    plt.bar(summary["border_friction"], summary["estimated_travel_hours"])
    plt.ylabel("Mean estimated travel hours")
    plt.title("Synthetic route delay by border friction")
    _save(path)


def plot_aid_type_coverage(aid_coverage: pd.DataFrame, path: str | Path) -> None:
    ordered = aid_coverage.sort_values("coverage_ratio")
    plt.figure(figsize=(10, 5))
    plt.bar(ordered["aid_type"], ordered["coverage_ratio"])
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Coverage ratio")
    plt.title("Aid type coverage")
    _save(path)
