# Marathon Planner API

FastAPI backend for the marathon training planner. Pure Python — no Streamlit.

## Local development

```bash
cd api
pip install -r requirements.txt

# Set Strava credentials (get from https://www.strava.com/settings/api)
export STRAVA_CLIENT_ID=your_id
export STRAVA_CLIENT_SECRET=your_secret

# Run dev server with auto-reload
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Endpoints

- `GET /api/plans` — list available plans
- `GET /api/plan/{plan_key}/schedule?race_date=...&long_dow=...` — full schedule
- `POST /api/workout-detail` — parse a workout into structured segments with paces
- `POST /api/auth/strava/exchange` — exchange OAuth code for tokens
- `POST /api/auth/strava/refresh` — refresh access token
- `GET /api/strava/activities?access_token=...` — fetch user's recent runs

## Deploy

Set environment variables:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `ALLOWED_ORIGINS` (comma-separated, e.g. `https://marathonplanner.vercel.app`)

Run with: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Compatible with Railway, Render, Fly.io, or any platform that runs Python.
