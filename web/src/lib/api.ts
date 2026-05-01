/**
 * API client. All backend calls go through here.
 * Set VITE_API_BASE in .env.local for local dev (e.g. http://localhost:8000)
 */

const API_BASE = import.meta.env.VITE_API_BASE || ''

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })
  if (!r.ok) {
    const text = await r.text()
    throw new Error(`API ${r.status}: ${text}`)
  }
  return r.json()
}

export interface Plan {
  key: string
  kind: string
  name: string
  weeks: number
  peak_mpw: number
  desc: string
}

export interface Run {
  date: string
  t: string         // run type: easy/long/tempo/vo2/race/me_primary/etc.
  m: number         // miles
  note?: string
}

export interface Schedule {
  plan_key: string
  plan: Plan
  plan_start: string
  race_date: string
  days: Run[]
}

export interface WorkoutSegment {
  label: string
  distance: string
  pace: string
  detail: string
}

export interface WorkoutDetail {
  workout_type: string
  miles: number
  marathon_pace_secs: number
  fivek_pace_secs: number
  segments: WorkoutSegment[]
}

export interface StravaActivity {
  name: string
  miles: number
  moving_time: number
  pace_sec_per_mile: number
  hr?: number
  elev_ft: number
}

export interface StravaTokens {
  access_token: string
  refresh_token: string
  expires_at: number
  athlete?: any
}

export const api = {
  listPlans: () => req<Plan[]>('/api/plans'),

  getSchedule: (planKey: string, params: {
    race_date: string
    long_dow?: number
    quality_dow?: number
    rest_dow?: number
  }) => {
    const q = new URLSearchParams(params as any).toString()
    return req<Schedule>(`/api/plan/${planKey}/schedule?${q}`)
  },

  workoutDetail: (params: {
    workout_type: string
    miles: number
    goal_time: string
    note?: string
  }) => req<WorkoutDetail>('/api/workout-detail', {
    method: 'POST',
    body: JSON.stringify(params),
  }),

  stravaExchange: (code: string) => req<StravaTokens>('/api/auth/strava/exchange', {
    method: 'POST',
    body: JSON.stringify({ code }),
  }),

  stravaRefresh: (refresh_token: string) => req<StravaTokens>('/api/auth/strava/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token }),
  }),

  getActivities: (access_token: string) =>
    req<Record<string, StravaActivity[]>>(`/api/strava/activities?access_token=${access_token}`),
}
