
import pandas as pd
from pathlib import Path

DATA = Path("data")

assets = pd.read_csv(DATA / "assets.csv")
policies = pd.read_csv(DATA / "policies.csv")
claims = pd.read_csv(DATA / "claims.csv")
fx = pd.read_csv(DATA / "fx_rates.csv")

print("\n=== 1. DATE INVESTIGATION ===")

for col in ["loss_date", "reported_date"]:
    parsed = pd.to_datetime(
        claims[col],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    )

    invalid = claims[parsed.isna()]

    print(f"\n{col}")
    print("Invalid dates:", len(invalid))
    print("Examples:")
    print(invalid[col].head(15).to_list())

print("\n=== 2. NEGATIVE CLAIM AMOUNTS ===")

for col in ["paid_amount", "reserve_amount"]:
    negative = claims[claims[col] < 0]

    print(f"\n{col}")
    print("Negative records:", len(negative))
    print(negative[
        ["claim_id", "policy_id", col, "currency", "status"]
    ].head(20).to_string(index=False))

print("\n=== 3. INVALID RELATIONSHIPS ===")

missing_assets = policies[
    ~policies["asset_id"].isin(assets["asset_id"])
]

missing_policies = claims[
    ~claims["policy_id"].isin(policies["policy_id"])
]

print("Policies with missing assets:", len(missing_assets))
print("Claims with missing policies:", len(missing_policies))

print("\n=== 4. FX RATE COVERAGE ===")

fx["month"] = fx["month"].astype(str)

print("FX month range:", fx["month"].min(), "to", fx["month"].max())

print("Duplicate FX month/currency combinations:",
      fx.duplicated(["month", "currency"]).sum())

print("Non-positive FX rates:",
      (fx["rate_dkk_per_unit"] <= 0).sum())

print("\n=== 5. POLICY DATE VALIDATION ===")

for col in ["inception_date", "expiry_date"]:
    policies[col] = pd.to_datetime(
        policies[col],
        errors="coerce"
    )

invalid_dates = policies[
    (policies["inception_date"] > policies["expiry_date"])
    | policies["inception_date"].isna()
    | policies["expiry_date"].isna()
]

print("Policies with invalid date ranges:", len(invalid_dates))

print("\n=== 6. CLAIM STATUS / AMOUNT CHECKS ===")

print(
    claims.groupby("status")[
        ["paid_amount", "reserve_amount"]
    ].agg(["count", "sum", "min", "max"]).to_string()
)

print("\n=== ORPHANED CLAIM DETAILS ===")

orphan_claims = claims[
    ~claims["policy_id"].isin(policies["policy_id"])
].copy()

print("Total orphaned claims:", len(orphan_claims))

print("\nOrphaned claims by status:")
print(orphan_claims["status"].value_counts())

print("\nOrphaned claims by currency:")
print(orphan_claims["currency"].value_counts())

orphan_dates = pd.to_datetime(
    orphan_claims["loss_date"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
)

print("\nOrphaned claims by loss year:")
print(orphan_dates.dt.year.value_counts().sort_index())

print("\nOrphaned claims financial amounts:")
print(
    orphan_claims[
        ["paid_amount", "reserve_amount"]
    ].describe()
)

print("\nSample orphaned claims:")
print(orphan_claims.head(20).to_string(index=False))

print("\nInvestigation complete.")

