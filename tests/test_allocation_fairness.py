from aidalloc.fairness import coverage_table, fairness_audit
from aidalloc.optimizer import allocate_aid, unmet_need_table
from aidalloc.synthetic import SyntheticAidConfig, generate_synthetic_aid_data


def _sample():
    data = generate_synthetic_aid_data(SyntheticAidConfig(regions=12, warehouses=3, seed=5))
    return data["regions"], data["needs"], data["inventory"], data["routes"]


def test_allocation_respects_requested_need_and_stock():
    regions, needs, inventory, routes = _sample()
    plan = allocate_aid(regions, needs, inventory, routes, policy="fairness_aware")
    unmet = unmet_need_table(needs, plan)
    assert not plan.empty
    assert (unmet["allocated_units"] <= unmet["requested_units"]).all()
    total_by_stock = inventory.groupby("aid_type")["stock_units"].sum()
    total_by_plan = plan.groupby("aid_type")["allocated_units"].sum()
    for aid_type, allocated in total_by_plan.items():
        assert allocated <= total_by_stock.loc[aid_type]


def test_fairness_audit_has_expected_columns():
    regions, needs, inventory, routes = _sample()
    plan = allocate_aid(regions, needs, inventory, routes, policy="fairness_aware")
    audit = fairness_audit(regions, needs, plan)
    coverage = coverage_table(regions, needs, plan)
    assert {"country", "country_coverage_ratio", "country_coverage_gap", "allocation_disparity_index"}.issubset(audit.columns)
    assert len(coverage) == len(regions)
    assert (coverage["coverage_ratio"] >= 0).all()
