import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import { api, WorkoutDetail, Run, StravaActivity } from '../lib/api'
import { loadSettings } from '../lib/store'

export default function WorkoutDetailScreen() {
  const { date } = useParams<{ date: string }>()
  const [run, setRun] = useState<Run | null>(null)
  const [detail, setDetail] = useState<WorkoutDetail | null>(null)
  const [actuals, setActuals] = useState<StravaActivity[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!date) return
    const settings = loadSettings()
    if (!settings.race_date) return

    api.getSchedule(settings.selected_plan, {
      race_date: settings.race_date,
      long_dow: settings.long_dow,
      quality_dow: settings.quality_dow,
      rest_dow: settings.rest_dow,
    }).then(sched => {
      const found = sched.days.find(d => d.date === date)
      if (!found) { setErr('Workout not found'); return }
      setRun(found)
      return api.workoutDetail({
        workout_type: found.t,
        miles: found.m,
        goal_time: settings.goal_time,
        note: found.note,
      })
    }).then(d => { if (d) setDetail(d) }).catch(e => setErr(String(e)))

    if (settings.access_token) {
      api.getActivities(settings.access_token).then(byDate => {
        setActuals(byDate[date] || [])
      }).catch(() => {})
    }
  }, [date])

  if (err) return <ErrorPanel message={err}/>
  if (!run || !detail) return <Loading/>

  const dateObj = parseISO(date!)
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const isPast = date! <= todayStr
  const hasActual = actuals.length > 0
  const totalActMiles = actuals.reduce((s, a) => s + a.miles, 0)
  const totalActSeconds = actuals.reduce((s, a) => s + a.moving_time, 0)
  const avgActPace = totalActMiles > 0 ? totalActSeconds / totalActMiles : 0
  const avgHr = (() => {
    const withHr = actuals.filter(a => a.hr)
    if (withHr.length === 0) return null
    const totMi = withHr.reduce((s, a) => s + a.miles, 0)
    return Math.round(withHr.reduce((s, a) => s + (a.hr || 0) * a.miles, 0) / totMi)
  })()
  const totalElev = actuals.reduce((s, a) => s + a.elev_ft, 0)

  return (
    <div className="min-h-screen pb-24">
      <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <Link to="/" className="text-strava font-semibold">← Back</Link>
        <div className="text-base font-semibold text-gray-900">{format(dateObj, 'EEE, MMM d')}</div>
      </header>

      <div className="px-4 py-4 space-y-4">
        {/* Headline card */}
        <div className="card text-center">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-2">{labelFor(run.t)}</div>
          <div className="text-5xl font-light text-gray-900">{run.m}<span className="text-2xl text-gray-500 ml-1">mi</span></div>
          <div className="text-xs text-gray-400 mt-1">planned</div>
          {run.note && (
            <div className="mt-3 text-sm text-gray-600 leading-relaxed">{run.note}</div>
          )}
        </div>

        {hasActual && (
          <HowItWent
            run={run}
            detail={detail}
            totalMiles={totalActMiles}
            totalSeconds={totalActSeconds}
            avgPace={avgActPace}
            avgHr={avgHr}
            totalElev={totalElev}
            activities={actuals}
          />
        )}

        {!hasActual && isPast && (
          <div className="card bg-red-50 border-red-200 text-center">
            <div className="text-sm font-semibold text-red-700">Workout missed</div>
            <div className="text-xs text-red-600 mt-1">No Strava activity recorded for this day.</div>
          </div>
        )}

        <div className="card">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-2">Your paces</div>
          <div className="grid grid-cols-2 gap-3">
            <PaceItem label="Marathon pace" pace={fmtPace(detail.marathon_pace_secs)}/>
            <PaceItem label="5K pace (est.)" pace={fmtPace(detail.fivek_pace_secs)}/>
          </div>
        </div>

        <div className="card">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-3">Planned workout</div>
          <div className="space-y-3">
            {detail.segments.map((s, i) => (
              <SegmentRow key={i} segment={s}/>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function HowItWent({
  run, detail, totalMiles, totalSeconds, avgPace, avgHr, totalElev, activities
}: {
  run: Run
  detail: WorkoutDetail
  totalMiles: number
  totalSeconds: number
  avgPace: number
  avgHr: number | null
  totalElev: number
  activities: StravaActivity[]
}) {
  const target = paceTargetFor(run.t, detail.marathon_pace_secs)

  const distPct = (totalMiles / run.m) * 100
  const distLabel = distPct >= 95 ? 'On target' : distPct >= 80 ? `${Math.round(distPct)}% of plan` : `${Math.round(distPct)}% — well short`
  const distColor = distPct >= 95 ? 'text-emerald-700' : distPct >= 80 ? 'text-amber-700' : 'text-red-700'

  let paceLabel: string | null = null
  let paceColor = 'text-gray-700'
  if (target && avgPace > 0) {
    if (avgPace >= target.lo && avgPace <= target.hi) {
      paceLabel = `In target range`
      paceColor = 'text-emerald-700'
    } else if (avgPace < target.lo) {
      const fasterBy = target.lo - avgPace
      paceLabel = `${Math.round(fasterBy)}s/mi faster than target`
      paceColor = run.t === 'easy' || run.t === 'long' ? 'text-amber-700' : 'text-emerald-700'
    } else {
      const slowerBy = avgPace - target.hi
      paceLabel = `${Math.round(slowerBy)}s/mi slower than target`
      paceColor = run.t === 'easy' || run.t === 'long' ? 'text-emerald-700' : 'text-amber-700'
    }
  }

  return (
    <div className="card border-emerald-200 bg-emerald-50/30">
      <div className="text-[10px] uppercase tracking-wider text-emerald-700 mb-3 font-semibold">✓ How it went</div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <Stat label="Distance" value={`${totalMiles.toFixed(2)} mi`} sub={distLabel} subColor={distColor}/>
        <Stat label="Avg pace" value={`${fmtPace(avgPace)}/mi`} sub={paceLabel || ' '} subColor={paceColor}/>
      </div>

      {target && (
        <div className="text-[10px] text-gray-500 mb-3">
          Target pace: <span className="font-mono text-gray-700">{fmtPace(target.lo)}–{fmtPace(target.hi)}/mi</span>
        </div>
      )}

      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-emerald-100">
        <Stat label="Time" value={fmtTime(totalSeconds)} small/>
        <Stat label="Avg HR" value={avgHr ? `${avgHr} bpm` : '—'} small/>
        <Stat label="Elev" value={totalElev > 0 ? `${totalElev.toLocaleString()} ft` : '—'} small/>
      </div>

      {activities.length > 1 && (
        <div className="pt-3 mt-3 border-t border-emerald-100 space-y-1.5">
          <div className="text-[10px] uppercase tracking-wider text-gray-500">Activities ({activities.length})</div>
          {activities.map((a, i) => (
            <div key={i} className="flex justify-between items-baseline text-xs">
              <span className="text-gray-700 truncate flex-1 mr-2">{a.name}</span>
              <span className="font-mono text-gray-600 shrink-0">{a.miles.toFixed(2)}mi · {fmtPace(a.pace_sec_per_mile)}/mi</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function paceTargetFor(workoutType: string, mpSecs: number): { lo: number; hi: number } | null {
  switch (workoutType) {
    case 'easy':
      return { lo: mpSecs + 60, hi: mpSecs + 90 }
    case 'long':
      return { lo: mpSecs + 45, hi: mpSecs + 75 }
    case 'tempo':
      return { lo: mpSecs - 25, hi: mpSecs - 15 }
    case 'vo2':
      return { lo: mpSecs - 70, hi: mpSecs - 50 }
    case 'race':
      return { lo: mpSecs - 5, hi: mpSecs + 5 }
    case 'me_primary':
    case 'me_secondary':
    case 'me_weekend':
      return null
    default:
      return null
  }
}

function Stat({ label, value, sub, subColor, small = false }: {
  label: string; value: string; sub?: string; subColor?: string; small?: boolean
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-gray-500">{label}</div>
      <div className={`font-mono font-semibold text-gray-900 ${small ? 'text-sm' : 'text-lg'}`}>{value}</div>
      {sub && sub !== ' ' && <div className={`text-[10px] mt-0.5 ${subColor || 'text-gray-500'}`}>{sub}</div>}
    </div>
  )
}

function SegmentRow({ segment }: { segment: { label: string; distance: string; pace: string; detail: string } }) {
  return (
    <div className="border-l-2 border-strava/30 pl-3 py-1">
      <div className="flex items-baseline justify-between gap-2">
        <div className="font-semibold text-sm text-gray-900 flex-1">{segment.label}</div>
        <div className="font-mono text-xs text-gray-700 shrink-0">{segment.distance}</div>
      </div>
      {segment.pace && segment.pace !== '—' && (
        <div className="text-xs font-mono text-strava font-semibold mt-0.5">{segment.pace}</div>
      )}
      {segment.detail && (
        <div className="text-xs text-gray-600 mt-1 leading-relaxed">{segment.detail}</div>
      )}
    </div>
  )
}

function PaceItem({ label, pace }: { label: string; pace: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-gray-400">{label}</div>
      <div className="text-base font-mono font-semibold text-gray-900">{pace}/mi</div>
    </div>
  )
}

function fmtPace(secs: number) {
  const m = Math.floor(secs / 60)
  const s = Math.round(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

function fmtTime(secs: number) {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = Math.round(secs % 60)
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m}:${s.toString().padStart(2, '0')}`
}

function labelFor(t: string) {
  return ({
    easy: 'Easy run', long: 'Long run', tempo: 'Lactate threshold', vo2: 'VO₂ max',
    race: 'Race day',
    me_primary: 'Primary workout', me_secondary: 'Secondary workout', me_weekend: 'Weekend workout',
  } as Record<string, string>)[t] || 'Run'
}

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin w-8 h-8 border-2 border-strava border-t-transparent rounded-full"/>
    </div>
  )
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <div className="text-red-500 mb-2">{message}</div>
      <Link to="/" className="text-strava font-semibold mt-4">Back to home</Link>
    </div>
  )
}
