"""Load, validate, and normalize the source data."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


class DataValidationError(ValueError):
    """Raised when source data cannot be trusted for calculations."""


@dataclass(frozen=True)
class LoadedData:
    assets: pd.DataFrame
    policies: pd.DataFrame
    claims: pd.DataFrame
    fx_rates: pd.DataFrame

    @property
    def orphaned_claims(self) -> pd.DataFrame:
        """Return claims whose policy reference cannot be resolved."""
        return self.claims[self.claims["is_orphaned"]].copy()


_REQUIRED_COLUMNS = {
    "assets": {
        "asset_id",
        "portfolio_id",
        "region",
        "asset_type",
        "construction_year",
        "sum_insured_dkk",
    },
    "policies": {
        "policy_id",
        "asset_id",
        "peril",
        "inception_date",
        "expiry_date",
        "annual_premium",
        "currency",
    },
    "claims": {
        "claim_id",
        "policy_id",
        "loss_date",
        "reported_date",
        "paid_amount",
        "reserve_amount",
        "currency",
        "status",
    },
    "fx_rates": {"month", "currency", "rate_dkk_per_unit"},
}


def load_data(data_dir: str | Path = "data") -> LoadedData:
    """Read and normalize the four source CSVs from ``data_dir``."""
    data_path = Path(data_dir)
    frames = {
        name: _read_csv(data_path / f"{name}.csv", columns)
        for name, columns in _REQUIRED_COLUMNS.items()
    }

    assets = frames["assets"]
    policies = frames["policies"]
    claims = frames["claims"]
    fx_rates = frames["fx_rates"]

    _validate_unique_ids(assets, "asset_id")
    _validate_unique_ids(policies, "policy_id")
    _validate_unique_ids(claims, "claim_id")

    policies["peril"] = _normalize_text(policies["peril"])
    policies["currency"] = _normalize_text(policies["currency"])
    claims["currency"] = _normalize_text(claims["currency"])
    claims["status"] = _normalize_text(claims["status"])

    policies["inception_date"] = _parse_dates(policies["inception_date"], "inception_date")
    policies["expiry_date"] = _parse_dates(policies["expiry_date"], "expiry_date")
    claims["loss_date"] = _parse_dates(claims["loss_date"], "loss_date")
    claims["reported_date"] = _parse_dates(claims["reported_date"], "reported_date")
    fx_rates["month"] = _parse_dates(fx_rates["month"], "month", month_only=True).dt.to_period("M")
    fx_rates["currency"] = _normalize_text(fx_rates["currency"])

    if (policies["inception_date"] > policies["expiry_date"]).any():
        raise DataValidationError("Policies contain invalid date ranges")
    _validate_positive(fx_rates["rate_dkk_per_unit"], "FX rates")
    if fx_rates.duplicated(["month", "currency"]).any():
        raise DataValidationError("FX rates contain duplicate month/currency keys")

    if policies["asset_id"].isin(assets["asset_id"]).eq(False).any():
        raise DataValidationError("Policies contain unknown asset references")

    claims["is_orphaned"] = ~claims["policy_id"].isin(policies["policy_id"])

    return LoadedData(
        assets=assets,
        policies=policies,
        claims=claims,
        fx_rates=fx_rates,
    )


def _read_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    if not path.exists():
        raise DataValidationError(f"Missing data file: {path}")

    frame = pd.read_csv(path)
    missing = required_columns.difference(frame.columns)
    if missing:
        raise DataValidationError(f"{path.name} is missing columns: {sorted(missing)}")
    return frame


def _validate_unique_ids(frame: pd.DataFrame, column: str) -> None:
    if frame[column].isna().any() or frame[column].duplicated().any():
        raise DataValidationError(f"{column} must contain unique, non-null values")


def _normalize_text(values: pd.Series) -> pd.Series:
    return values.astype("string").str.strip().str.lower()


def _parse_dates(values: pd.Series, column: str, month_only: bool = False) -> pd.Series:
    parsed = pd.to_datetime(
        values,
        format="%Y-%m" if month_only else "mixed",
        dayfirst=not month_only,
        errors="coerce",
    )
    if parsed.isna().any():
        raise DataValidationError(f"{column} contains invalid dates")
    return parsed


def _validate_positive(values: pd.Series, label: str) -> None:
    if values.isna().any() or (values <= 0).any():
        raise DataValidationError(f"{label} must be positive and non-null")