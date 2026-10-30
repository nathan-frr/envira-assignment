# Envira loss-experience service

## Setup

From the repository root:

```bash
python -m venv .venv
source .venv/Scripts/activate        # Git Bash
pip install fastapi uvicorn pandas
```

On PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

Place `assets.csv`, `policies.csv`, `claims.csv`, and `fx_rates.csv` in `data/`. The data files are not included in the repository.

## Run

```bash
python -m uvicorn app.main:app --reload
```

The service runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Endpoints

```text
GET /portfolios/{portfolio_id}/loss-experience
GET /portfolios/loss-experience
```

Example:

```bash
curl http://127.0.0.1:8000/portfolios/PF-01/loss-experience
```

All monetary values are returned in DKK. Data-quality decisions and exclusions are documented in [REPORT.md](REPORT.md).