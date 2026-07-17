"""Run the complete synthetic cross-border disaster aid allocation lab.

This command uses only fictional data. It demonstrates needs scoring, logistics
and border-delay simulation, baseline and fairness-aware allocation, unmet-need
analysis, cross-border fairness auditing, transparency logging, and local reports
without using real humanitarian information.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aidalloc.audit import append_record, verify_log
from aidalloc.config import ensure_output_dirs, set_seed
from aidalloc.fairness import aid_type_coverage, coverage_table, fairness_audit, summary_metrics
from aidalloc.logistics import route_summary
from aidalloc.optimizer import allocate_aid, compare_policies, unmet_need_table
from aidalloc.reporting import write_report
from aidalloc.scoring import score_needs
from aidalloc.synthetic import SyntheticAidConfig, generate_synthetic_aid_data
from aidalloc.visualization import plot_aid_type_coverage, plot_allocation_coverage, plot_fairness_gaps, plot_logistics_delay, plot_need_urgency


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a synthetic cross-border disaster aid allocation simulator.")
    parser.add_argument("--regions", type=int, default=24)
    parser.add_argument("--warehouses", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--policy", default="fairness_aware", choices=["fairness_aware", "urgency_first"])
    args = parser.parse_args()

    set_seed(args.seed)
    data = generate_synthetic_aid_data(SyntheticAidConfig(regions=args.regions, warehouses=args.warehouses, seed=args.seed))
    regions = data["regions"]
    warehouses = data["warehouses"]
    inventory = data["inventory"]
    needs = data["needs"]
    routes = data["routes"]
    actors = data["actors"]

    scored_needs = score_needs(regions, needs)
    allocation = allocate_aid(regions, needs, inventory, routes, policy=args.policy)
    unmet = unmet_need_table(needs, allocation)
    fairness = fairness_audit(regions, needs, allocation)
    coverage = coverage_table(regions, needs, allocation)
    aid_coverage = aid_type_coverage(needs, allocation)
    logistics = route_summary(routes)
    comparison = compare_policies(regions, needs, inventory, routes)
    summary = summary_metrics(regions, needs, allocation, fairness)
    summary.update({
        "policy": args.policy,
        "seed": args.seed,
        "warehouse_count": int(len(warehouses)),
        "route_count": int(len(routes)),
        "data_origin": "synthetic fictional humanitarian allocation data",
        "humanitarian_boundary": "research planning evidence only; not an official aid allocation decision",
    })

    outputs = ensure_output_dirs(args.output_dir)
    regions.to_csv(outputs["results"] / "synthetic_regions.csv", index=False)
    warehouses.to_csv(outputs["results"] / "synthetic_warehouses.csv", index=False)
    inventory.to_csv(outputs["results"] / "synthetic_aid_inventory.csv", index=False)
    routes.to_csv(outputs["results"] / "synthetic_routes.csv", index=False)
    needs.to_csv(outputs["results"] / "synthetic_needs.csv", index=False)
    actors.to_csv(outputs["results"] / "synthetic_actors.csv", index=False)
    scored_needs.to_csv(outputs["results"] / "synthetic_scored_needs.csv", index=False)
    allocation.to_csv(outputs["results"] / "synthetic_allocation_plan.csv", index=False)
    unmet.to_csv(outputs["results"] / "synthetic_unmet_need.csv", index=False)
    fairness.to_csv(outputs["results"] / "synthetic_fairness_audit.csv", index=False)
    coverage.to_csv(outputs["results"] / "synthetic_region_coverage.csv", index=False)
    aid_coverage.to_csv(outputs["results"] / "synthetic_aid_type_coverage.csv", index=False)
    logistics.to_csv(outputs["results"] / "synthetic_logistics_summary.csv", index=False)
    comparison.to_csv(outputs["results"] / "synthetic_policy_comparison.csv", index=False)

    audit_path = outputs["audit"] / "allocation_audit_log.jsonl"
    append_record(audit_path, {**summary, "boundary": "synthetic aid allocation experiment only"})
    summary["audit_log"] = verify_log(audit_path)
    (outputs["results"] / "synthetic_aid_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    write_report(outputs["reports"] / "synthetic_aid_report.md", summary, allocation, unmet, fairness, logistics, comparison)
    plot_need_urgency(scored_needs, outputs["figures"] / "synthetic_need_urgency.png")
    plot_allocation_coverage(coverage, outputs["figures"] / "synthetic_allocation_coverage.png")
    plot_fairness_gaps(fairness, outputs["figures"] / "synthetic_fairness_gaps.png")
    plot_logistics_delay(routes, outputs["figures"] / "synthetic_logistics_delay.png")
    plot_aid_type_coverage(aid_coverage, outputs["figures"] / "synthetic_aid_type_coverage.png")
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
