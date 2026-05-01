# Marathon Planner

Personalized marathon training plans with Strava integration.
PWA — install to your home screen on iOS or Android.

## Structure

```
api/    FastAPI backend with all training plan logic
web/    React PWA frontend
```

## Quick start

### Backend
```bash
cd api
pip install -r requirements.txt
export STRAVA_CLIENT_ID=...
export STRAVA_CLIENT_SECRET=...
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd web
npm install
cp .env.example .env.local   # set VITE_API_BASE and VITE_STRAVA_CLIENT_ID
npm run dev                  # http://localhost:5173
```

## Deploying

- **Backend**: Railway, Render, or Fly.io. Set `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`,
  and `ALLOWED_ORIGINS` env vars. Run `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Frontend**: Vercel, root directory `web`. Set `VITE_API_BASE` to your backend URL
  and `VITE_STRAVA_CLIENT_ID`.

## Plans supported

- Pfitzinger 18/55, 18/70, 12/55, 12/70 (configurable rest/quality/long days)
- Marathon Excellence Gale 70/80 and Tornado 85/95
