# Marathon Planner Web

Mobile-first PWA built with React + Vite + Tailwind. Calls the FastAPI backend.

## Local development

```bash
cd web
npm install
cp .env.example .env.local
# edit .env.local with your VITE_API_BASE and VITE_STRAVA_CLIENT_ID

npm run dev    # http://localhost:5173
```

## Build for production

```bash
npm run build
# Output in dist/
```

## Deploy

**Vercel (recommended)**:
1. Connect your GitHub repo
2. Set "Root Directory" to `web`
3. Add env vars: `VITE_API_BASE` (your deployed API URL), `VITE_STRAVA_CLIENT_ID`
4. Deploy

The PWA manifest auto-generates. Users can "Add to Home Screen" on iOS/Android
to install it as an app.

## Strava OAuth setup

In your Strava API settings (https://www.strava.com/settings/api), add the
authorization callback domain: `your-deployment.vercel.app` (without https://).
