import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, Plan } from '../lib/api'
import { loadSettings, saveSettings, clearSettings, UserSettings } from '../lib/store'

const DOWS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

export default function SettingsScreen() {
  const nav = useNavigate()
  const [settings, setSettings] = useState<UserSettings>(() => loadSettings())
  const [plans, setPlans] = useState<Plan[]>([])

  useEffect(() => { api.listPlans().then(setPlans).catch(() => {}) }, [])

  function update<K extends keyof UserSettings>(key: K, value: UserSettings[K]) {
    const next = { ...settings, [key]: value }
    setSettings(next)
    saveSettings(next)
  }

  function connectStrava() {
    const clientId = import.meta.env.VITE_STRAVA_CLIENT_ID
    const redirect = `${window.location.origin}/auth/callback`
    const url = `https://www.strava.com/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirect)}&response_type=code&scope=activity:read_all,profile:read_all`
    window.location.href = url
  }

  function disconnect() {
    saveSettings({ access_token: undefined, refresh_token: undefined, athlete: undefined })
    setSettings(loadSettings())
  }

  function reset() {
    if (confirm('Reset all settings? This will sign out of Strava and clear your plan choices.')) {
      clearSettings()
      nav('/')
    }
  }

  // Validation
  const conflicts: string[] = []
  if (settings.long_dow === settings.quality_dow) conflicts.push("Long and quality can't be the same day")
  if (settings.rest_dow === settings.long_dow) conflicts.push("Rest can't be on long run day")
  if (settings.rest_dow === settings.quality_dow) conflicts.push("Rest can't be on quality day")
  const longQualityGap = Math.min(
    Math.abs(settings.long_dow - settings.quality_dow),
    7 - Math.abs(settings.long_dow - settings.quality_dow)
  )
  const advisories: string[] = []
  if (longQualityGap > 0 && longQualityGap < 2) {
    advisories.push(`Quality is ${longQualityGap} day(s) from long run — aim for 3+ for recovery`)
  }

  const isMe = plans.find(p => p.key === settings.selected_plan)?.kind === 'me'

  return (
    <div className="min-h-screen pb-24">
      <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <Link to="/" className="text-strava font-semibold">← Back</Link>
        <div className="text-base font-semibold text-gray-900">Settings</div>
      </header>

      <div className="px-4 py-4 space-y-4">
        {/* Strava */}
        <Section title="Strava">
          {settings.access_token ? (
            <div>
              <div className="flex items-center gap-3 mb-3">
                {settings.athlete?.profile && <img src={settings.athlete.profile} className="w-10 h-10 rounded-full"/>}
                <div>
                  <div className="font-semibold text-gray-900">{settings.athlete?.firstname} {settings.athlete?.lastname}</div>
                  <div className="text-xs text-gray-500">Connected</div>
                </div>
              </div>
              <button onClick={disconnect} className="text-sm text-red-600 active:text-red-800">Disconnect</button>
            </div>
          ) : (
            <button onClick={connectStrava} className="w-full bg-strava text-white py-3 rounded-xl font-semibold active:bg-strava-dark">
              Connect Strava
            </button>
          )}
        </Section>

        {/* Race details */}
        <Section title="Race">
          <Field label="Goal time">
            <input type="text" value={settings.goal_time} onChange={e => update('goal_time', e.target.value)}
              placeholder="3:30:00" className="bg-transparent text-right text-gray-900 font-mono"/>
          </Field>
          <Field label="Race date">
            <input type="date" value={settings.race_date} onChange={e => update('race_date', e.target.value)}
              className="bg-transparent text-right text-gray-900"/>
          </Field>
        </Section>

        {/* Plan picker */}
        <Section title="Training plan">
          <div className="space-y-1">
            {plans.length === 0 && (
              <div className="text-sm text-gray-400 py-3 text-center">Loading plans...</div>
            )}
            {plans.map(p => {
              const selected = settings.selected_plan === p.key
              return (
                <button key={p.key}
                  type="button"
                  onClick={() => update('selected_plan', p.key)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all active:scale-[0.98] ${selected ? 'bg-strava/10 border-2 border-strava' : 'border-2 border-transparent bg-gray-50 active:bg-gray-100'}`}>
                  <div>
                    <div className={`font-semibold ${selected ? 'text-strava' : 'text-gray-900'}`}>{p.name}</div>
                    <div className="text-xs text-gray-500">{p.desc}</div>
                  </div>
                  {selected && (
                    <div className="w-6 h-6 rounded-full bg-strava flex items-center justify-center shrink-0 ml-2">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </Section>

        {/* Day-of-week customization (Pfitz only) */}
        {!isMe && (
          <Section title="Schedule" subtitle="Pick which day each type of run lands on">
            <DowField label="Long run" value={settings.long_dow} onChange={v => update('long_dow', v)}/>
            <DowField label="Quality workout" value={settings.quality_dow} onChange={v => update('quality_dow', v)}/>
            <DowField label="Rest day" value={settings.rest_dow} onChange={v => update('rest_dow', v)}/>
            {conflicts.map(c => <Warning key={c} text={c} blocking/>)}
            {advisories.map(a => <Warning key={a} text={a}/>)}
          </Section>
        )}

        <button onClick={reset} className="w-full text-sm text-gray-500 py-3 active:text-red-600">
          Reset all settings
        </button>
      </div>
    </div>
  )
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="card">
      <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-1">{title}</div>
      {subtitle && <div className="text-xs text-gray-500 mb-3">{subtitle}</div>}
      <div className={subtitle ? '' : 'mt-2'}>{children}</div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <div className="text-sm text-gray-700">{label}</div>
      {children}
    </div>
  )
}

function DowField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="py-2 border-b border-gray-100 last:border-0">
      <div className="text-sm text-gray-700 mb-2">{label}</div>
      <div className="grid grid-cols-7 gap-1">
        {DOWS.map((d, i) => (
          <button key={d} onClick={() => onChange(i)}
            className={`py-2 rounded-lg text-xs font-semibold ${value === i ? 'bg-strava text-white' : 'bg-gray-100 text-gray-600 active:bg-gray-200'}`}>
            {d}
          </button>
        ))}
      </div>
    </div>
  )
}

function Warning({ text, blocking = false }: { text: string; blocking?: boolean }) {
  const cls = blocking ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
  return <div className={`mt-2 px-3 py-2 rounded-lg text-xs ${cls}`}>{text}</div>
}
