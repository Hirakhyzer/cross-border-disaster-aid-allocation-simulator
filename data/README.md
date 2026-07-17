# Data Boundary

This repository does not include real disaster, humanitarian, border, route, warehouse, or affected-population datasets.

Future real-data adapters should use local-only ignored paths such as `data/raw/` and include metadata:

```text
region_id
country
region_name
population
affected_population
vulnerability_index
infrastructure_damage
access_constraint
aid_type
requested_units
warehouse_id
stock_units
route_id
distance_km
border_friction
estimated_travel_hours
source
license
collection_date
privacy_review_status
```

Real data requires authorization, data minimization, protection of affected people, and humanitarian partner validation.
