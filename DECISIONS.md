Started: 2026-10-30 14:10 TZ
Stopped: 2026-10-30 16:10 TZ

## What I built
Generated scripts to analyze the data with pandas to find anomalies and considerations that should be taken for implementation
Implemented the data loader, with validation and normalization considerations based on data analysis, checked numbers of loaded assets, claims, rates, oprhaned claims, peril categories
Implemented the calculation for each portfolio grouped by peril, checked metrics on an example with PF-01
Implemented the first endpoint, tested on the browser with PF-01

Implemented the single-portfolio loss-experience endpoint and an all-portfolio comparison endpoint.
The comparison ranks portfolios by loss ratio descending, then incurred loss descending, then portfolio ID.
Premiums and claims are aggregated separately, and orphaned claims are excluded from portfolio results.
AI tooling was used for implementation support; I independently verified the loaded row counts, orphan count, peril normalization and PF-01 API response.

## What I deliberately did not build, and why

I did not build a frontend, database, Docker setup, or additional filters because the core API and financial correctness were the priority.

## What I would do first with another day

I would add focused automated tests, an independent verification script, and a data-quality report endpoint.