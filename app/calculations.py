"""Financial calculations for portfolio loss experience."""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from app.data_loader import LoadedData


@dataclass(frozen=True)
class PerilResult:
    peril: str
    policy_count: int
    earned_premium_dkk: Decimal
    incurred_loss_dkk: Decimal
    loss_ratio: Decimal | None
    claim_count: int
    largest_claim_dkk: Decimal | None


@dataclass(frozen=True)
class PortfolioResult:
    portfolio_id: str
    policy_count: int
    earned_premium_dkk: Decimal
    incurred_loss_dkk: Decimal
    loss_ratio: Decimal | None
    claim_count: int
    largest_claim_dkk: Decimal | None


def calculate_portfolio(data: LoadedData, portfolio_id: str) -> list[PerilResult]:
    """Calculate loss experience by peril for one portfolio.

    Orphaned claims remain in ``data`` for reporting but cannot be attributed
    to this result because their policy and peril are unknown.
    """
    portfolio_assets = data.assets[data.assets["portfolio_id"] == portfolio_id]
    portfolio_policies = data.policies[
        data.policies["asset_id"].isin(portfolio_assets["asset_id"])
    ].copy()
    if portfolio_policies.empty:
        return []

    fx_lookup = _build_fx_lookup(data.fx_rates)
    premium_by_peril = defaultdict(lambda: Decimal("0"))
    policy_count_by_peril = defaultdict(int)

    for policy in portfolio_policies.itertuples(index=False):
        premium = _to_decimal(policy.annual_premium)
        rate = _fx_rate(fx_lookup, policy.inception_date, policy.currency)
        premium_by_peril[policy.peril] += premium * rate
        policy_count_by_peril[policy.peril] += 1

    valid_claims = data.claims[
        (~data.claims["is_orphaned"])
        & data.claims["policy_id"].isin(portfolio_policies["policy_id"])
    ].copy()
    claim_metrics = _calculate_claims(valid_claims, portfolio_policies, fx_lookup)

    return [
        PerilResult(
            peril=peril,
            policy_count=policy_count_by_peril[peril],
            earned_premium_dkk=_money(premium_by_peril[peril]),
            incurred_loss_dkk=_money(claim_metrics[peril]["loss"]),
            loss_ratio=_loss_ratio(premium_by_peril[peril], claim_metrics[peril]["loss"]),
            claim_count=claim_metrics[peril]["count"],
            largest_claim_dkk=(
                _money(claim_metrics[peril]["largest"])
                if claim_metrics[peril]["largest"] is not None
                else None
            ),
        )
        for peril in sorted(policy_count_by_peril)
    ]


def calculate_portfolio_summary(
    data: LoadedData, portfolio_id: str
) -> PortfolioResult:
    """Aggregate one portfolio across all of its perils."""
    peril_results = calculate_portfolio(data, portfolio_id)
    if not peril_results:
        return PortfolioResult(
            portfolio_id=portfolio_id,
            policy_count=0,
            earned_premium_dkk=Decimal("0.00"),
            incurred_loss_dkk=Decimal("0.00"),
            loss_ratio=None,
            claim_count=0,
            largest_claim_dkk=None,
        )

    earned_premium = sum(
        (result.earned_premium_dkk for result in peril_results), Decimal("0")
    )
    incurred_loss = sum(
        (result.incurred_loss_dkk for result in peril_results), Decimal("0")
    )
    largest_claims = [
        result.largest_claim_dkk
        for result in peril_results
        if result.largest_claim_dkk is not None
    ]
    return PortfolioResult(
        portfolio_id=portfolio_id,
        policy_count=sum(result.policy_count for result in peril_results),
        earned_premium_dkk=earned_premium,
        incurred_loss_dkk=incurred_loss,
        loss_ratio=_loss_ratio(earned_premium, incurred_loss),
        claim_count=sum(result.claim_count for result in peril_results),
        largest_claim_dkk=max(largest_claims) if largest_claims else None,
    )


def calculate_all_portfolios(data: LoadedData) -> list[PortfolioResult]:
    """Return all portfolios ranked by loss ratio and incurred loss."""
    portfolio_ids = sorted(data.assets["portfolio_id"].unique())
    results = [calculate_portfolio_summary(data, portfolio_id) for portfolio_id in portfolio_ids]
    return sorted(
        results,
        key=lambda result: (
            result.loss_ratio is None,
            -(result.loss_ratio or Decimal("0")),
            -result.incurred_loss_dkk,
            result.portfolio_id,
        ),
    )


def _calculate_claims(
    claims: pd.DataFrame,
    policies: pd.DataFrame,
    fx_lookup: dict[tuple[pd.Period, str], Decimal],
) -> defaultdict:
    policy_perils = policies.set_index("policy_id")["peril"]
    metrics = defaultdict(lambda: {"loss": Decimal("0"), "count": 0, "largest": None})

    for claim in claims.itertuples(index=False):
        peril = policy_perils[claim.policy_id]
        incurred = _incurred_loss(claim.status, claim.paid_amount, claim.reserve_amount)
        incurred_dkk = incurred * _fx_rate(fx_lookup, claim.loss_date, claim.currency)
        metrics[peril]["loss"] += incurred_dkk
        metrics[peril]["count"] += 1
        if metrics[peril]["largest"] is None or incurred_dkk > metrics[peril]["largest"]:
            metrics[peril]["largest"] = incurred_dkk

    return metrics


def _incurred_loss(status: str, paid_amount: object, reserve_amount: object) -> Decimal:
    if status in {"withdrawn", "declined"}:
        return Decimal("0")
    if status == "settled":
        return _to_decimal(paid_amount)
    if status == "open":
        return _to_decimal(paid_amount) + _to_decimal(reserve_amount)
    raise ValueError(f"Unsupported claim status: {status}")


def _build_fx_lookup(fx_rates: pd.DataFrame) -> dict[tuple[pd.Period, str], Decimal]:
    return {
        (row.month, row.currency): _to_decimal(row.rate_dkk_per_unit)
        for row in fx_rates.itertuples(index=False)
    }


def _fx_rate(
    fx_lookup: dict[tuple[pd.Period, str], Decimal], date: pd.Timestamp, currency: str
) -> Decimal:
    key = (date.to_period("M"), currency)
    try:
        return fx_lookup[key]
    except KeyError as error:
        raise ValueError(f"Missing FX rate for {currency} in {key[0]}") from error


def _loss_ratio(premium: Decimal, loss: Decimal) -> Decimal | None:
    if premium == 0:
        return None
    return (loss / premium).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)