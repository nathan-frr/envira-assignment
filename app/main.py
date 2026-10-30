from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from app.calculations import PerilResult, calculate_portfolio
from app.data_loader import LoadedData, load_data


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class PerilLossExperience(BaseModel):
	peril: str
	policy_count: int
	earned_premium_dkk: float
	incurred_loss_dkk: float
	loss_ratio: float | None
	claim_count: int
	largest_claim_dkk: float | None


class PortfolioLossExperience(BaseModel):
	portfolio_id: str
	currency: str
	results: list[PerilLossExperience]


@asynccontextmanager
async def lifespan(app: FastAPI):
	app.state.data = load_data(DATA_DIR)
	yield


app = FastAPI(
	title="Envira Loss Experience Service",
	lifespan=lifespan,
)


@app.get(
	"/portfolios/{portfolio_id}/loss-experience",
	response_model=PortfolioLossExperience,
)
def get_portfolio_loss_experience(
	portfolio_id: str,
	request: Request,
) -> PortfolioLossExperience:
	data: LoadedData = request.app.state.data
	if portfolio_id not in set(data.assets["portfolio_id"]):
		raise HTTPException(status_code=404, detail="Portfolio not found")

	results = calculate_portfolio(data, portfolio_id)
	return PortfolioLossExperience(
		portfolio_id=portfolio_id,
		currency="DKK",
		results=[_to_response(result) for result in results],
	)


def _to_response(result: PerilResult) -> PerilLossExperience:
	return PerilLossExperience(
		peril=result.peril,
		policy_count=result.policy_count,
		earned_premium_dkk=result.earned_premium_dkk,
		incurred_loss_dkk=result.incurred_loss_dkk,
		loss_ratio=result.loss_ratio,
		claim_count=result.claim_count,
		largest_claim_dkk=result.largest_claim_dkk,
	)
