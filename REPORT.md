# Data-quality report

## Scope and policy

This report documents the source-data issues found while building the loss-experience calculations and how they affect the API results. The source rows are not rewritten or deleted. Instead, the loader keeps the data available for inspection and the calculation applies the attribution rule described below.

## Rows excluded from portfolio results

### 260 orphaned claims

`claims.csv` contains 4,509 claims. 260 claims (5.77%) reference a `policy_id` that does not exist in `policies.csv`.

These claims are excluded from portfolio and peril calculations because there is no reliable way to determine their policy, asset, portfolio, or peril. Including them would either misattribute loss to an arbitrary portfolio or require an unsupported inference.

The orphaned claims are all:

- `settled` status
- DKK-denominated
- from loss year 2023
- DKK 11,662,789.17 total paid amount
- DKK 0.00 total reserve amount

They remain in the loaded data with `is_orphaned = True` so that a future data-quality endpoint can report them. `calculate_portfolio` filters those rows before joining claims to policy perils.

No assets, policies, or FX rows were excluded from the calculations.

## Issues retained rather than excluded

### Negative settled payments

There are 262 settled claims with a negative `paid_amount`, including values down to DKK -218,151.44. These were retained as signed financial transactions rather than silently converting them to positive values or dropping them. They may represent recoveries, corrections, or other reversals and should be reviewed with the source-system owner. Under the current definition, a settled claim's incurred loss is its paid amount, so the negative value affects the result.

### Withdrawn and declined claims

The 327 withdrawn and 246 declined claims are retained and counted as claims, but their incurred loss is DKK 0.00 under the brief's definition. They are not excluded rows; they are zero-cost claims.

### Repeated foreign keys

Multiple policies per asset and multiple claims per policy are expected relationships, not duplicate-record errors. The unique identifiers themselves are valid: `asset_id`, `policy_id`, and `claim_id` have unique keys in their owning files.

## Normalization and validation performed

- Peril, currency, and status text is stripped and lower-cased. This collapses 25 raw peril spellings to the five intended perils without dropping rows.
- Mixed date spellings such as `2023-01-25` and `14-02-2023` are parsed successfully. There are no invalid dates, and no policy has an expiry before its inception.
- All policies reference an existing asset.
- FX rates have complete, positive month/currency keys with no duplicates for the dates and currencies used by the source data.
- There are no missing values or fully duplicated rows in the source files.