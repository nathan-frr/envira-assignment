
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

FILES = [
    "assets.csv",
    "policies.csv",
    "claims.csv",
    "fx_rates.csv",
]



def inspect_file(filename):
    path = DATA_DIR / filename

    print("\n" + "=" * 90)
    print(f"FILE: {filename}")
    print("=" * 90)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return None

    df = pd.read_csv(path)

    # Basic information
    print(f"\nRows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(
        f"Memory usage: "
        f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    )

    # Schema
    print("\n--- SCHEMA ---")
    print(df.dtypes.to_string())

    # Sample records
    print("\n--- FIRST 5 ROWS ---")
    print(df.head().to_string(index=False))

    # Missing values
    print("\n--- MISSING VALUES ---")
    missing = df.isna().sum()
    missing = missing[missing > 0]

    if missing.empty:
        print("No missing values")
    else:
        print(missing.to_string())

    # Duplicate rows
    print("\n--- DUPLICATES ---")
    print(f"Fully duplicated rows: {df.duplicated().sum()}")

    # Unique values and cardinality
    print("\n--- COLUMN CARDINALITY ---")

    for col in df.columns:
        print(
            f"{col}: {df[col].nunique(dropna=False)} unique values"
        )

    # Categorical values
    print("\n--- CATEGORICAL / LOW CARDINALITY VALUES ---")

    for col in df.columns:
        if df[col].nunique() <= 30:
            print(f"\n{col}:")
            print(
                df[col]
                .value_counts(dropna=False)
                .to_string()
            )

    # Peril normalization investigation
    if "peril" in df.columns:
        print("\n--- NORMALIZED PERILS ---")

        normalized = (
            df["peril"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        print("\nNormalized peril counts:")
        print(normalized.value_counts(dropna=False).to_string())

        print("\nOriginal distinct values:", df["peril"].nunique())
        print("Normalized distinct values:", normalized.nunique())

    # Potential duplicate identifiers
    print("\n--- POTENTIAL DUPLICATE IDENTIFIERS ---")

    identifier_columns = [
        "id",
        "asset_id",
        "policy_id",
        "claim_id"
    ]

    for col in identifier_columns:
        if col in df.columns:
            duplicates = df[col].duplicated(keep=False).sum()

            print(
                f"{col}: {duplicates} rows with duplicated IDs"
            )

    # Date columns
    print("\n--- DATE COLUMNS ---")

    date_columns = [
        col for col in df.columns
        if (
            "date" in col.lower()
            or col.lower() in [
                "inception",
                "expiry",
                "month"
            ]
        )
    ]

    for col in date_columns:
        if col == "month":
            dates = pd.to_datetime(
                df[col],
                format="%Y-%m",
                errors="coerce"
            )
        else:
            dates = pd.to_datetime(
                df[col],
                format="mixed",
                dayfirst=True,
                errors="coerce"
            )

        invalid_count = dates.isna().sum()

        print(f"\n{col}")
        print(f"Invalid/missing dates: {invalid_count}")
        print(f"Minimum: {dates.min()}")
        print(f"Maximum: {dates.max()}")

        if invalid_count > 0:
            print("Invalid date examples:")
            print(df.loc[dates.isna(), col].head(10).to_list())

    # Numeric columns
    print("\n--- NUMERIC SUMMARY ---")

    numeric = df.select_dtypes(include="number")

    if not numeric.empty:
        print(numeric.describe().to_string())

        # Investigate negative numeric values
        print("\n--- NEGATIVE NUMERIC VALUES ---")

        for col in numeric.columns:
            negative = df[df[col] < 0]

            if not negative.empty:
                print(f"\n{col}: {len(negative)} negative values")
                print(negative[col].head(10).to_list())

    return df


def inspect_relationships(data):
    print("\n" + "=" * 90)
    print("RELATIONSHIP CHECKS")
    print("=" * 90)

    assets = data.get("assets.csv")
    policies = data.get("policies.csv")
    claims = data.get("claims.csv")

    if assets is not None and policies is not None:
        print("\n--- POLICIES -> ASSETS ---")

        missing = ~policies["asset_id"].isin(assets["asset_id"])

        print("Missing asset references:", missing.sum())

        print("Policies per asset:")
        print(policies["asset_id"].value_counts().describe())

    if policies is not None and claims is not None:
        print("\n--- CLAIMS -> POLICIES ---")

        missing = ~claims["policy_id"].isin(policies["policy_id"])

        print("Missing policy references:", missing.sum())

        print("Claims per policy:")
        print(claims["policy_id"].value_counts().describe())

    if assets is not None:
        print("\n--- PORTFOLIOS ---")
        print(assets["portfolio_id"].value_counts().to_string())


def main():
    print("ENVIRA DATA EXPLORATION")
    print(f"Data directory: {DATA_DIR.resolve()}")

    data = {}

    for filename in FILES:
        df = inspect_file(filename)

        if df is not None:
            data[filename] = df

    inspect_relationships(data)

    print("\n" + "=" * 90)
    print("EXPLORATION COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()
