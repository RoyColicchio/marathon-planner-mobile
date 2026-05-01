"""
Marathon Planner API — FastAPI backend
Ports the training plan logic from the Streamlit app into REST endpoints.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta, datetime
from typing import Optional
import os
import requests

from plans import PLANS, build_planned_map
from workouts import workout_segments, parse_me_segments, fivek_pace_secs

app = FastAPI(title="Marathon Planner API", version="1.0.0")

# CORS — allow frontend at any origin during dev. Tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STRAVA_CLIENT_ID     = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")


# ── helpers ───────────────────────────────────────────────────────
def goal_pace_secs(goal_time: str) -> int:
    """Convert 'h:mm:ss' goal time to seconds per mile."""
    parts = goal_time.split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = parts[0], parts[1], "0"
    else:
        raise ValueError(f"invalid goal_time: {goal_time}")
    total = int(h) * 3600 + int(m) * 60 + int(s)
    return round(total / 26.2)


# ── plan endpoints ────────────────────────────────────────────────
@app.get("/api/plans")
def list_plans():
    """Return all available training plans with metadata."""
    return [
        {"key": k, **v}
        for k, v in PLANS.items()
    ]


@app.get("/api/plan/{plan_key}/schedule")
def get_schedule(
    plan_key: str,
    race_date: str = Query(..., description="ISO date string YYYY-MM-DD"),
    long_dow: int = Query(0, ge=0, le=6, description="0=Sun, 1=Mon, ..., 6=Sat"),
    quality_dow: int = Query(3, ge=0, le=6),
    rest_dow: int = Query(1, ge=0, le=6),
):
    """Return the full week-by-week schedule for a plan.
    Each day in the response includes date, run type, miles, optional workout note.
    """
    if plan_key not in PLANS:
        raise HTTPException(status_code=404, detail=f"unknown plan: {plan_key}")

    try:
        planned_map, plan_start = build_planned_map(
            plan_key, race_date,
            long_day=long_dow, quality_day=quality_dow, rest_day=rest_dow,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "plan_key": plan_key,
        "plan": PLANS[plan_key],
        "plan_start": plan_start,
        "race_date": race_date,
        "days": [
            {"date": ds, **run}
            for ds, run in sorted(planned_map.items())
        ],
    }


class WorkoutDetailRequest(BaseModel):
    workout_type: str        # easy / long / tempo / vo2 / race / me_primary / etc.
    miles: float
    goal_time: str           # "h:mm:ss"
    note: Optional[str] = None


@app.post("/api/workout-detail")
def workout_detail(req: WorkoutDetailRequest):
    """Return structured workout segments (warmup, intervals, recovery, cooldown)
    with pace ranges calculated from the user's marathon goal time.
    """
    try:
        gps = goal_pace_secs(req.goal_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    segments = workout_segments(req.workout_type, req.miles, gps, note=req.note)
    return {
        "workout_type": req.workout_type,
        "miles": req.miles,
        "marathon_pace_secs": gps,
        "fivek_pace_secs": round(fivek_pace_secs(gps)),
        "segments": [
            {"label": s[0], "distance": s[1], "pace": s[2], "detail": s[3]}
            for s in segments
        ],
    }


# ── Strava endpoints ──────────────────────────────────────────────
class StravaExchangeRequest(BaseModel):
    code: str


@app.post("/api/auth/strava/exchange")
def strava_exchange(req: StravaExchangeRequest):
    """Exchange an OAuth authorization code for access + refresh tokens."""
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": req.code,
        "grant_type": "authorization_code",
    })
    data = r.json()
    if "access_token" not in data:
        raise HTTPException(status_code=400, detail=data.get("message", "auth failed"))
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": data["expires_at"],
        "athlete": data.get("athlete", {}),
    }


class StravaRefreshRequest(BaseModel):
    refresh_token: str


@app.post("/api/auth/strava/refresh")
def strava_refresh(req: StravaRefreshRequest):
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": req.refresh_token,
        "grant_type": "refresh_token",
    })
    data = r.json()
    if "access_token" not in data:
        raise HTTPException(status_code=401, detail=data.get("message", "refresh failed"))
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": data["expires_at"],
    }


@app.get("/api/strava/activities")
def get_activities(
    access_token: str = Query(...),
    days_back: int = Query(65, ge=1, le=180),
):
    """Fetch the user's recent runs from Strava."""
    since = int((datetime.utcnow() - timedelta(days=days_back)).timestamp())
    all_acts, page = [], 1
    while True:
        r = requests.get(
            f"https://www.strava.com/api/v3/athlete/activities"
            f"?per_page=100&after={since}&page={page}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        all_acts.extend(a for a in data if a.get("type") == "Run" or a.get("sport_type") == "Run")
        if len(data) < 100:
            break
        page += 1

    # Group by local date
    by_date = {}
    for a in all_acts:
        ds = (a.get("start_date_local") or "")[:10]
        if not ds or not a.get("distance"):
            continue
        miles = a["distance"] / 1609.34
        by_date.setdefault(ds, []).append({
            "name": a.get("name", "Run"),
            "miles": round(miles, 2),
            "moving_time": a.get("moving_time", 0),
            "pace_sec_per_mile": round(a.get("moving_time", 0) / miles) if miles > 0 else 0,
            "hr": a.get("average_heartrate"),
            "elev_ft": round((a.get("total_elevation_gain") or 0) * 3.28084),
        })
    return by_date


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"name": "Marathon Planner API", "docs": "/docs"}
