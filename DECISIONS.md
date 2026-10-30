Started: 2026-10-30 14:10
Stopped: 2026-10-30 16:10

## What I built
Generated scripts to analyze the data with pandas to find anomalies and considerations that should be taken for implementation
Implemented the data loader, with validation and normalization considerations based on data analysis, checked numbers of loaded assets, claims, rates, oprhaned claims, peril categories
Implemented the calculation for each portfolio grouped by peril, checked metrics on an example with PF-01
Implemented the first endpoint, tested on the browser with PF-01
Implemented the single-portfolio loss-experience endpoint and an all-portfolio comparison endpoint.
Converted monetary values to DKK using monthly FX rates: policy inception month for premiums and loss month for claims.
The comparison ranks by loss ratio descending, then incurred loss descending, then portfolio ID.
Orphaned claims are retained for inspection but excluded from portfolio results because they cannot be attributed to a policy or peril.
Added REPORT.md to document the data-quality findings and exclusion policy.
AI tooling was used for implementation support; I independently verified row counts, orphan count, peril normalization, and the PF-01 API response.

## What I deliberately did not build, and why

I did not build a frontend, database, Docker setup, additional filters, or a data-quality endpoint because the core API and financial correctness were the priority.

## What I would do first with another day

I would add focused automated tests, an independent verification script, and a data-quality endpoint exposing the report metrics.