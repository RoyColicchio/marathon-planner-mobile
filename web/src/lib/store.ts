/**
 * LocalStorage-backed user settings.
 * Architected with the same swap-friendly interface as the Streamlit app —
 * later we can swap this for a server-backed store with no UI changes.
 */

export interface UserSettings {
  goal_time: string
  race_date: string
  selected_plan: string
  long_dow: number       // 0=Sun, 1=Mon, ..., 6=Sat
  quality_dow: number
  rest_dow: number
  // Strava
  access_token?: string
  refresh_token?: string
  token_expires_at?: number
  athlete?: any
}

const KEY = 'marathon_planner_state_v2'

const DEFAULTS: UserSettings = {
  goal_time: '3:30:00',
  race_date: '',
  selected_plan: 'pfitz-18-55',
  long_dow: 0,
  quality_dow: 3,
  rest_dow: 1,
}

export function loadSettings(): UserSettings {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { ...DEFAULTS }
    return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULTS }
  }
}

export function saveSettings(s: Partial<UserSettings>) {
  const current = loadSettings()
  const merged = { ...current, ...s }
  localStorage.setItem(KEY, JSON.stringify(merged))
  return merged
}

export function clearSettings() {
  localStorage.removeItem(KEY)
}
