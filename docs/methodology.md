# Methodology

This project studies synthetic cross-border humanitarian aid allocation. The method is intentionally transparent and reproducible.

## Data model

The lab generates fictional regions, countries, warehouses, aid inventory, routes, border delays, and aid needs. No real humanitarian dataset is included.

## Need scoring

Each region-aid pair receives a score based on requested units, vulnerability, infrastructure damage, access constraints, and event recency. This is a planning proxy only.

## Logistics model

Each warehouse-region route includes distance, route risk, border friction, customs delay, and travel-time estimate. Routes are not operational instructions.

## Allocation policies

Two policies are compared:

- `urgency_first`: need, urgency, vulnerability, and route access.
- `fairness_aware`: urgency-first plus minimum-service targets and country coverage balancing.

## Fairness metrics

The lab computes country coverage gaps, minimum-service violation rate, vulnerability-weighted coverage, region neglect risk, and allocation disparity.

## Transparency

Each run writes CSV outputs, figures, a Markdown report, and a hash-chained audit log. The audit log provides local tamper-evidence for experiment records.

## Limitations

The metrics are synthetic research signals. They are not moral, legal, or operational conclusions and must not be used for real humanitarian decision-making without expert review and field validation.
