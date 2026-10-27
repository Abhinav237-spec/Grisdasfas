# UK Day-Ahead Wind Forecast Portal

A web app that helps a UK energy utility's day-ahead purchasing team (1) see the latest national wind forecast available at decision time, and (2) quantify how accurate those forecasts have been, so the error can be factored into buying decisions.

- **Scope:** national-level wind only, Elexon data only (`FUELHH` actuals, `WINDFOR` forecasts)
- **Decision window:** purchase decisions made in **January 2026** for delivery on the following day (delivery days 2 Jan to 1 Feb 2026)
- **Stack:** React (frontend), Python / FastAPI (backend), Docker

> **Status:** work in progress, tracked in the sprint milestones on the Issues tab.

## Live app

Link to the deployed app: _to be added (Sprint 3)_

## Key assumption

A day-ahead decision for delivery day D is made on D-1 at a configurable cutoff (default 09:00 UK time). For every target half-hour, the forecast used is the one with the latest `publishTime` at or before that cutoff.

## Repository layout

| Path | Purpose |
|---|---|
| `backend/` | FastAPI service, analysis code and tests |
| `frontend/` | React (Vite) app |
| `scripts/` | Data fetch (`fetch_data.py`) and exploration (`explore.py`) scripts |
| `notebooks/` | Exploration notebooks |
| `data/raw/` | Raw Elexon downloads (git-ignored if large) |
| `docs/` | Planning and design notes (`docs/SPRINTS.md`) |
| `docker-compose.yml` | Local run of backend and frontend (added in Sprint 3) |

## How to start

_Filled in as the app is built. Data setup, once available:_

```bash
python -m venv .venv && source .venv/bin/activate
pip install pandas requests
python scripts/fetch_data.py      # downloads Elexon data into data/raw/
python scripts/explore.py         # prints schema, cadence and quality checks
```

## AI tool disclosure

AI tools (Claude) were used to assist with planning, code generation and documentation for this project.
